function gomoku_selftest()
% Pure MATLAB tactical/timeline smoke test (no video), distinct from detector test.
board=zeros(15,15);
board(8,4:7)=1; % D8 to G8; C8 or H8 is a direct win.
assert(localWin(board,8,3,1));
assert(localWin(board,8,8,1));
assert(~localWin(board,8,9,1));
assert(nnz(board)==4);
% Regression for MATLAB error 'Duplicate dimension and variable name: Row'.
t=table((1:2)',[25;43],string(["Black";"White"]),[8;7],[8;9], ...
        string(["H8";"I7"]),'VariableNames', ...
        {'Index','Frame','Color','Row','Col','Position'}, ...
        'DimensionNames',{'MoveRecords','Variables'});
assert(strcmp(t.Properties.VariableNames{4},'Row'));
assert(height(t)==2);
frames=[25,43,61,79,949];
assert(nnz(frames<=24)==0);
assert(nnz(frames<=25)==1);
assert(nnz(frames<=949)==5);
fprintf('MATLAB_SELFTEST_PASS: tactical win and frame/move timeline\n');
end

function result=localWin(board,r,c,color)
if board(r,c)~=0,result=false;return;end
board(r,c)=color;result=false;
dirs=[1,0;0,1;1,1;1,-1];
for k=1:4
    for shift=-4:0
        rr=r+(shift:shift+4)*dirs(k,1);
        cc=c+(shift:shift+4)*dirs(k,2);
        if all(rr>=1 & rr<=15 & cc>=1 & cc<=15)
            if all(board(sub2ind(size(board),rr,cc))==color)
                result=true;return;
            end
        end
    end
end
end
