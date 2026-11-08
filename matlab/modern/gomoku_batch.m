function gomoku_batch(configFile)
% GOMOKU_BATCH Independent MATLAB video recognizer for GomokuVision V0.3.4.
% Requires licensed MATLAB R2021b+ and Image Processing Toolbox.
% Accepts JSON config from WPF / -batch; NO Python or C# detector is invoked.
% Writes the SAME six-column moves.csv and summary.json contract.
if nargin < 1 || ~isfile(configFile)
    error('GomokuVision:Config', 'Specify a valid JSON config file.');
end
opts = jsondecode(fileread(configFile));
needed = {'input','calibration','black_template','white_template','output_dir'};
for i = 1:numel(needed)
    if ~isfield(opts, needed{i}) || ~isfile(opts.(needed{i})) && ~strcmp(needed{i},'output_dir')
        error('GomokuVision:Input','Input not available: %s', needed{i});
    end
end
if ~exist(opts.output_dir,'dir'), mkdir(opts.output_dir); end
if exist('normxcorr2','file') ~= 2 || exist('imresize','file') ~= 2
    error('GomokuVision:Toolbox','Image Processing Toolbox is required.');
end
opts = fillDefaults(opts);
pts = readCalibration(opts.calibration);
blackTemplate = toGray(imread(opts.black_template));
whiteTemplate = toGray(imread(opts.white_template));
templates = {imresize(blackTemplate,opts.scale), imresize(whiteTemplate,opts.scale)};
for i = 1:2
    if min(size(templates{i})) < 3 || std(double(templates{i}(:))) < 0.1
        error('GomokuVision:Template','Template too small or not textured.');
    end
end
video = VideoReader(opts.input);
outputFile=fullfile(opts.output_dir,'output.mp4');
w = VideoWriter(outputFile,'MPEG-4');
w.FrameRate = max(1,video.FrameRate/opts.sample_every);
open(w);
closer = onCleanup(@()close(w));
board = zeros(15,15); counts = zeros(15,15,2);
moves = zeros(225,4); % [source frame, color, row, col]
moveCount = 0; numRead = 0; numAnalyzed = 0; matchAttemptsTotal = 0; canceled = false;
lastPreview=''; lastProgressMoves=-1; wallClock=tic;
recognitionSeconds=0; % sum of NCC detection + confirmed move updates only
% Each run gets its own immutable preview directory. WPF is allowed to keep
% previously published PNGs open while MATLAB writes the next frame.
previewRoot=fullfile(opts.output_dir,'preview_frames');
if ~isfolder(previewRoot), mkdir(previewRoot); end
previewDir=tempname(previewRoot);
mkdir(previewDir);
try
    while hasFrame(video)
        if ~isempty(opts.cancel_file) && isfile(opts.cancel_file)
            canceled=true; break;
        end
        frame=readFrame(video); numRead=numRead+1;
        if mod(numRead-1,opts.sample_every)~=0, continue; end
        numAnalyzed=numAnalyzed+1;
        fullScan=mod(numAnalyzed-1,opts.full_scan_every)==0;
        if isempty(findWinner(board))
            recognitionClock=tic;
            [detected,counts,attempts] = findMoves(frame,board,pts,templates,counts,opts,fullScan,moves(1:moveCount,:));
            matchAttemptsTotal=matchAttemptsTotal+attempts;
            for k=1:size(detected,1)
                r=detected(k,1); c=detected(k,2); color=detected(k,3);
                if board(r,c)==0
                    board(r,c)=color;
                    moveCount=moveCount+1;
                    moves(moveCount,:)=[numRead,color,r,c];
                end
            end
            recognitionSeconds=recognitionSeconds+toc(recognitionClock);
        end
        % Overlay uses confirmed locations, never simulated or model-inferred detections.
        annotated=paintRecognition(frame,board,pts,opts.overlay_mode);
        writeVideo(w,annotated);
        if numAnalyzed==1 || mod(numAnalyzed,5)==0 || moveCount~=lastProgressMoves || ~hasFrame(video)
            lastPreview=fullfile(previewDir,sprintf('frame_%06d.png',numRead));
            imwrite(annotated,lastPreview); % immutable preview with green confirmed-move rectangles
            writeProgress(opts,numRead,video,numAnalyzed,moveCount,lastPreview,moves(1:moveCount,:));
            lastProgressMoves=moveCount;
        end
    end
    if moveCount==0, warning('GomokuVision:Empty','No stones recognized.'); end
    clear closer;
    makeResult(opts,board,moves(1:moveCount,:),numRead,numAnalyzed,video.FrameRate,toc(wallClock),canceled,matchAttemptsTotal,recognitionSeconds);
    if numAnalyzed>0
        % Save a stable offline thumbnail once (not a live, repeatedly
        % overwritten preview). Keep progress on the immutable last snapshot.
        imwrite(annotated,fullfile(opts.output_dir,'last_frame.png'));
        if isempty(lastPreview)
            lastPreview=fullfile(opts.output_dir,'last_frame.png');
        end
        writeProgress(opts,numRead,video,numAnalyzed,moveCount,lastPreview,moves(1:moveCount,:));
    end
    fprintf('MATLAB_ENGINE_COMPLETE: %d moves / %d analyzed frames\n',moveCount,numAnalyzed);
catch ex
    clear closer;
    rethrow(ex);
end
end

function o=fillDefaults(o)
if ~isfield(o,'sample_every'), o.sample_every=6; end
if ~isfield(o,'full_scan_every'), o.full_scan_every=4; end
if ~isfield(o,'confirmations'), o.confirmations=2; end
if ~isfield(o,'local_radius'), o.local_radius=6; end
if ~isfield(o,'scale'), o.scale=0.5; end
if ~isfield(o,'black_threshold'), o.black_threshold=0.65; end
if ~isfield(o,'white_threshold'), o.white_threshold=0.75; end
if ~isfield(o,'progress_file'), o.progress_file=''; end
if ~isfield(o,'cancel_file'), o.cancel_file=''; end
if ~isfield(o,'roi_mode'), o.roi_mode='separated'; end
if ~isfield(o,'overlay_mode'), o.overlay_mode='recognition_prediction'; end
if ~any(strcmp(o.roi_mode,{'shared','separated'})) || ...
   ~any(strcmp(o.overlay_mode,{'recognition','recognition_prediction'}))
    error('GomokuVision:Config','Unknown ROI/overlay mode');
end
if o.sample_every<1 || o.full_scan_every<1 || o.confirmations<1 || o.scale<=0 || o.scale>1
    error('GomokuVision:Config','Invalid sampling, confirmation, or image scale.');
end
end

function g=toGray(img)
if ndims(img)==3, g=rgb2gray(img); else, g=img; end
end

function points=readCalibration(filename)
t = readtable(filename,'TextType','string');
if height(t)~=225, error('GomokuVision:Calibration','Expected 225 calibration coordinates.'); end
points=nan(15,15,2);
for i=1:height(t)
    label=char(strtrim(t.Label(i)));
    if numel(label)<2 || label(1)<'A' || label(1)>'O'
        error('GomokuVision:Calibration','Invalid legacy point label.');
    end
    % LEGACY csv label row(letter) and column(number), not regular move notation.
    r=double(label(1))-64;
    c=str2double(label(2:end));
    if isnan(c) || c<1 || c>15 || any(isfinite(points(r,c,:)))
        error('GomokuVision:Calibration','Duplicate or invalid board point.');
    end
    points(r,c,1)=t.x(i);
    points(r,c,2)=t.y(i);
end
if any(~isfinite(points(:))), error('GomokuVision:Calibration','Incomplete calibration.'); end
end

function [found, counts, attempts]=findMoves(frame,board,points,templates,counts,opts,fullScan,history)
gray = imresize(toGray(frame),opts.scale);
found = zeros(0,3); attempts=0;
recent = zeros(0,2);
for color=1:2
    idx=find(history(:,2)==color,1,'last');
    if ~isempty(idx), recent(end+1,:)=history(idx,3:4); end %#ok<AGROW>
end
if isempty(recent),recent=[8,8];end
for r=1:15
    for c=1:15
        if board(r,c)~=0,continue;end
        if ~fullScan && ~isempty(history) && ~any(all(abs(recent-[r,c])<=opts.local_radius,2))
            continue;
        end
        x=round(points(r,c,1)*opts.scale);
        y=round(points(r,c,2)*opts.scale);
        if x<2 || y<2 || x>size(gray,2)-1 || y>size(gray,1)-1
            counts(r,c,:)=0; continue;
        end
        maxTemplate=max([size(templates{1}),size(templates{2})]);
        radius=max(4,round(maxTemplate*0.7));
        region=double(gray(max(1,y-radius):min(end,y+radius), max(1,x-radius):min(end,x+radius)));
        center=double(gray(y-1:y+1,x-1:x+1));
        centerMean=mean(center(:)); background=median(region(:));
        % FAST GATE: a bare board-crossing is dark in its central 3x3 pixels,
        % causing thousands of unnecessary normxcorr2 calls. A broader disk
        % distinguishes a full dark stone from two thin grid lines. Keep the
        % original bright-center white gate for low-contrast white stones.
        darkDisk=double(gray(max(1,y-7):min(size(gray,1),y+7), ...
                             max(1,x-7):min(size(gray,2),x+7)));
        diskMean=mean(darkDisk(:));
        blackAllowed=diskMean<background-20 || diskMean<80;
        whiteAllowed=centerMean>background+20 || centerMean>205;
        if ~blackAllowed && ~whiteAllowed
            counts(r,c,:)=0;continue;
        end
        scores=[-1,-1];
        for color=1:2
            if strcmp(opts.roi_mode,'separated') && color==1 && ~blackAllowed,continue;end
            if strcmp(opts.roi_mode,'separated') && color==2 && ~whiteAllowed,continue;end
            templ=double(templates{color});
            [th,tw]=size(templ);pad=max(th,tw);
            x1=max(1,x-pad);x2=min(size(gray,2),x+pad);
            y1=max(1,y-pad);y2=min(size(gray,1),y+pad);
            roi=double(gray(y1:y2,x1:x2));
            if size(roi,1)<th || size(roi,2)<tw,continue;end
            attempts=attempts+1;
            response=normxcorr2(templ,roi);
            % Keep only matches with the ENTIRE template inside ROI.
            valid=response(th:size(roi,1),tw:size(roi,2));
            [score, idx]=max(valid(:));
            [offsetY,offsetX]=ind2sub(size(valid),idx);
            cx=x1+offsetX-1+(tw-1)/2; cy=y1+offsetY-1+(th-1)/2;
            dx=spacing(points,r,c,2)*opts.scale;
            dy=spacing(points,r,c,1)*opts.scale;
            if abs(cx-x)<=max(2,0.4*dx) && abs(cy-y)<=max(2,0.4*dy)
                scores(color)=score;
            end
        end
        margin=[scores(1)-opts.black_threshold,scores(2)-opts.white_threshold];
        [value,chosen]=max(margin);
        for color=1:2
            if value>=0 && color==chosen
                counts(r,c,color)=counts(r,c,color)+1;
            else
                counts(r,c,color)=0;
            end
        end
        if value>=0 && counts(r,c,chosen)>=opts.confirmations
            found(end+1,:)=[r,c,chosen]; %#ok<AGROW>
            counts(r,c,:)=0;
        end
    end
end
end

function dist=spacing(p,r,c,axis)
if axis==2
    neighbors=[c-1,c+1]; neighbors=neighbors(neighbors>=1 & neighbors<=15);
    vals=arrayfun(@(k)abs(p(r,k,1)-p(r,c,1)),neighbors);
else
    neighbors=[r-1,r+1]; neighbors=neighbors(neighbors>=1 & neighbors<=15);
    vals=arrayfun(@(k)abs(p(k,c,2)-p(r,c,2)),neighbors);
end
if isempty(vals),dist=20;else,dist=max(1,min(vals));end
end

function line=findWinner(board)
line=[];
for r=1:15
    for c=1:15
        color=board(r,c);
        if color==0,continue;end
        directions=[1,0;0,1;1,1;1,-1];
        for k=1:4
            rr=r+(0:4)*directions(k,1);cc=c+(0:4)*directions(k,2);
            if all(rr>=1 & rr<=15 & cc>=1 & cc<=15)
                idx=sub2ind(size(board),rr,cc);
                if all(board(idx)==color)
                    line=[rr(:),cc(:)];return;
                end
            end
        end
    end
end
end

function suggestions=topSuggestions(board,color)
scored=zeros(0,3);
for r=1:15
    for c=1:15
        if board(r,c)~=0,continue;end
        if hypotheticalWin(board,r,c,color),score=10000000;
        elseif hypotheticalWin(board,r,c,3-color),score=5000000;
        else
            dist=abs(r-8)+abs(c-8);
            local=board(max(1,r-2):min(15,r+2),max(1,c-2):min(15,c+2));
            score=50*max(0,(3-dist)/3)+100*sum(local(:)==color)+20*sum(local(:)==3-color);
        end
        scored(end+1,:)=[score,r,c]; %#ok<AGROW>
    end
end
scored=sortrows(scored,[-1,2,3]);
n=min(5,size(scored,1));
suggestions=repmat(struct('position','','score',0),1,n);
for k=1:n
    suggestions(k).position=sprintf('%c%d',char(64+scored(k,3)),scored(k,2));
    suggestions(k).score=scored(k,1);
end
end

function yes=hypotheticalWin(board,r,c,color)
if board(r,c)~=0, yes=false;return;end
b=board;b(r,c)=color;yes=~isempty(findWinner(b));
end

function writeProgress(o,numRead,v,numAnalyzed,moveCount,preview,moves)
if isempty(o.progress_file),return;end
records=repmat(struct('frame',0,'color',0,'row',0,'col',0),1,moveCount);
for j=1:moveCount
    records(j)=struct('frame',moves(j,1),'color',moves(j,2), ...
        'row',moves(j,3),'col',moves(j,4));
end
progress=struct('frame',numRead,'total_frames',round(v.Duration*v.FrameRate), ...
    'analyzed_frames',numAnalyzed,'moves',moveCount,'preview_path',preview, ...
    'move_records',records);
try
    writeJson(o.progress_file,progress);
catch ex
    % Preview progress is best-effort; a transient reader or antivirus lock
    % must never destroy the complete MATLAB recognition run.
    warning('GomokuVision:Progress', 'Progress update delayed: %s',ex.message);
end
end

function makeResult(o,b,moves,numRead,numAnalyzed,fps,secs,canceled,matchAttemptsTotal,recognitionSeconds)
n=size(moves,1);
idx=(1:n)';frames=moves(:,1);rows=moves(:,3);cols=moves(:,4);
colors=strings(n,1); positions=strings(n,1);
for i=1:n
    if moves(i,2)==1, colors(i)="Black"; else, colors(i)="White"; end
    positions(i)=sprintf('%c%d',char(64+cols(i)),rows(i));
end
% MATLAB reserves 'Row' as a default table dimension name. Keep the public
% six-column CSV contract by giving dimensions non-conflicting names.
result=table(idx,frames,colors,rows,cols,positions,'VariableNames', ...
    {'Index','Frame','Color','Row','Col','Position'}, ...
    'DimensionNames',{'MoveRecords','Variables'});
writetable(result,fullfile(o.output_dir,'moves.csv'));
black=positions(colors=="Black");white=positions(colors=="White");
rounds=(1:max(numel(black),numel(white)))';
black(end+1:numel(rounds))="";white(end+1:numel(rounds))="";
writetable(table(rounds,black,white,'VariableNames',{'Round','Black','White'}), ...
    fullfile(o.output_dir,'moves_legacy.csv'));
win=findWinner(b); winner='';
if ~isempty(win)
    if b(win(1,1),win(1,2))==1,winner='Black';else,winner='White';end
end
report=struct('engine','matlab-native-ncc','input',o.input, ...
    'sampling_every',o.sample_every,'confirmations',o.confirmations, ...
    'confirmation_delay_frames',o.sample_every*(o.confirmations-1), ...
    'full_scan_every_processed_frames',o.full_scan_every, ...
    'frames_read',numRead,'frames_analyzed',numAnalyzed,'input_fps',fps, ...
    'wall_seconds',secs,'recognition_seconds',round(recognitionSeconds,4), ...
    'canceled',canceled,'moves',n, ...
    'roi_mode',o.roi_mode,'overlay_mode',o.overlay_mode, ...
    'match_attempts',matchAttemptsTotal, ...
    'black_moves',numel(positions(colors=="Black")), ...
    'white_moves',numel(positions(colors=="White")), ...
    'winner',winner,'black_suggestions',topSuggestions(b,1), ...
    'white_suggestions',topSuggestions(b,2), ...
    'accuracy_note','Native MATLAB recognition; requires independent manual validation.');
writeJson(fullfile(o.output_dir,'summary.json'),report);
% Image Processing Toolbox available (imwrite). Simple final board no third-party art.
canvas=uint8(ones(560,560,3)*211);
for k=1:15
    x=28+(k-1)*36;
    canvas(x,28:532,:)=80;
    canvas(28:532,x,:)=80;
end
[xx,yy]=meshgrid(1:560,1:560); % generate image coordinate grid just once
for i=1:n
    r=rows(i);c=cols(i);x=28+(c-1)*36;y=28+(r-1)*36;
    mask=(xx-x).^2+(yy-y).^2<=13^2;
    color=38;
    if colors(i)=="White",color=238;end
    for channel=1:3
        plane=canvas(:,:,channel);plane(mask)=color;canvas(:,:,channel)=plane;
    end
end
imwrite(canvas,fullfile(o.output_dir,'board_final.png'));
end

function writeJson(filename,data)
[folder,~,~]=fileparts(filename);
if ~isfolder(folder),mkdir(folder);end
content=jsonencode(data);
tmp=[tempname(folder),'.tmp'];
fid=fopen(tmp,'w','n','UTF-8');
if fid==-1,error('GomokuVision:Output','Cannot open JSON output.');end
fwrite(fid,content,'char');fclose(fid);
for attempt=1:8
    [ok,message]=movefile(tmp,filename,'f');
    if ok,return;end
    if attempt<8,pause(0.03*attempt);end
end
if isfile(tmp),delete(tmp);end
error('GomokuVision:Output','Cannot publish JSON %s: %s',filename,message);
end


function out=paintRecognition(frame,board,pts,overlayMode)
% Pure MATLAB RGB drawing. Green bounding boxes reflect CONFIRMED stones only.
% 'recognition' suppresses the predictor markers; 'recognition_prediction' adds them.
out=frame;
if ndims(out)==2, out=repmat(out,1,1,3); end
for r=1:15
    for c=1:15
        if board(r,c)==0,continue;end
        x=round(pts(r,c,1));y=round(pts(r,c,2));
        out=strokeRect(out,x-20,y-20,x+20,y+20,uint8([35,255,45]),3);
    end
end
win=findWinner(board);
if ~isempty(win)
    a=win(1,:);b=win(end,:);
    out=strokeLine(out,round(pts(a(1),a(2),1)),round(pts(a(1),a(2),2)), ...
                   round(pts(b(1),b(2),1)),round(pts(b(1),b(2),2)),uint8([255,30,30]));
elseif strcmp(overlayMode,'recognition_prediction') && any(board(:)~=0)
    % Cache heuristic suggestions until the BOARD actually changes. Re-running
    % full tactical evaluation for each sampled frame made MATLAB sluggish.
    persistent lastBoard cachedSuggestions
    if isempty(lastBoard) || ~isequal(lastBoard,board) || isempty(cachedSuggestions)
        cachedSuggestions={topSuggestions(board,1),topSuggestions(board,2)};
        lastBoard=board;
    end
    for side=1:2
        suggested=cachedSuggestions{side};
        if side==1,ink=uint8([20,240,50]);else,ink=uint8([20,255,255]);end
        for k=1:min(3,numel(suggested))
            label=char(suggested(k).position);col=double(label(1))-64;row=str2double(label(2:end));
            x=round(pts(row,col,1));y=round(pts(row,col,2));
            out=strokeRect(out,x-7,y-7,x+7,y+7,ink,2);
        end
    end
end
end

function out=strokeRect(out,x1,y1,x2,y2,ink,lineWidth)
% Draw VISIBLE green outlines; 1-pixel MATLAB outlines vanished after WPF
% displayed 720px frames at 220px. Every confirmed stone gets a 3px stroke.
if nargin<7,lineWidth=3;end
[h,w,~]=size(out);
x1=max(1,min(w,round(x1)));x2=max(1,min(w,round(x2)));
y1=max(1,min(h,round(y1)));y2=max(1,min(h,round(y2)));
if x1>x2 || y1>y2,return;end
th=min([lineWidth,x2-x1+1,y2-y1+1]);
for ch=1:3
    out(y1:y1+th-1,x1:x2,ch)=ink(ch);
    out(y2-th+1:y2,x1:x2,ch)=ink(ch);
    out(y1:y2,x1:x1+th-1,ch)=ink(ch);
    out(y1:y2,x2-th+1:x2,ch)=ink(ch);
end
end

function out=strokeLine(out,x1,y1,x2,y2,ink)
count=max(abs(x2-x1),abs(y2-y1))+1;
for i=linspace(0,1,max(2,count))
    x=round(x1+(x2-x1)*i);y=round(y1+(y2-y1)*i);
    if x<1 || y<1 || x>size(out,2) || y>size(out,1),continue;end
    out(y,x,:)=reshape(ink,1,1,3);
end
end
