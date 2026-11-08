using System;
using System.Collections.Generic;

namespace GomokuVision;

/// <summary>Pure frame/step synchronization logic, shared by the WPF player and .NET self-tests.</summary>
public static class PlaybackTimeline
{
    public static int FrameAt(int startFrame, double elapsedSeconds, double fps, double speed, int totalFrames)
    {
        if (totalFrames < 1 || !double.IsFinite(elapsedSeconds) || elapsedSeconds < 0 ||
            !double.IsFinite(fps) || fps <= 0 || !double.IsFinite(speed) || speed <= 0)
            throw new ArgumentOutOfRangeException(nameof(totalFrames), "Invalid playback timing");
        double next=startFrame+Math.Floor(elapsedSeconds*fps*speed);
        return (int)Math.Clamp(next,0,totalFrames-1);
    }

    public static int MoveCountAtFrame(IEnumerable<int> oneBasedMoveFrames, int zeroBasedFrame)
    {
        int count=0;
        foreach (int frame in oneBasedMoveFrames)
        {
            if (frame <= zeroBasedFrame+1) count++;
            else break;
        }
        return count;
    }
}
