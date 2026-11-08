using System;
using System.Collections.Generic;
using System.Linq;

namespace GomokuVision;

public sealed record Move(int Frame, int Color, int Row, int Col)
{
    public string Position => $"{(char)('A' + Col)}{Row + 1}";
}

public sealed record Suggestion(int Row, int Col, double Score)
{
    public string Position => $"{(char)('A' + Col)}{Row + 1}";
}

public sealed class Board
{
    public const int Size = 15;
    public int[,] Cells { get; } = new int[Size, Size];
    public List<Move> Moves { get; } = new();
    private static readonly (int dr, int dc)[] Directions = [(1, 0), (0, 1), (1, 1), (1, -1)];

    public void Place(int frame, int color, int row, int col)
    {
        if ((color != 1 && color != 2) || !Inside(row, col))
            throw new ArgumentOutOfRangeException(nameof(color), "Invalid color or coordinate");
        if (Cells[row, col] != 0)
            throw new InvalidOperationException("Occupied square");
        Cells[row, col] = color;
        Moves.Add(new Move(frame, color, row, col));
    }

    public (int Color, List<(int Row, int Col)> Line)? Winner()
    {
        for (int r = 0; r < Size; r++)
        for (int c = 0; c < Size; c++)
        {
            int color = Cells[r, c];
            if (color == 0) continue;
            foreach (var (dr, dc) in Directions)
            {
                var line = new List<(int Row, int Col)>();
                for (int k = 0; k < 5; k++)
                {
                    int rr = r + k * dr, cc = c + k * dc;
                    if (!Inside(rr, cc) || Cells[rr, cc] != color) break;
                    line.Add((rr, cc));
                }
                if (line.Count == 5) return (color, line);
            }
        }
        return null;
    }

    public List<Suggestion> Suggestions(int player, int top = 5)
    {
        if (player != 1 && player != 2)
            throw new ArgumentOutOfRangeException(nameof(player));
        var suggestions = new List<Suggestion>();
        for (int r = 0; r < Size; r++)
        for (int c = 0; c < Size; c++)
            if (Cells[r, c] == 0) suggestions.Add(new Suggestion(r, c, Evaluate(r, c, player)));
        return suggestions.OrderByDescending(x => x.Score)
                          .ThenBy(x => x.Row).ThenBy(x => x.Col).Take(top).ToList();
    }

    private double Evaluate(int r, int c, int player)
    {
        int opponent = 3 - player, moveCount = Moves.Count;
        // Tactical priority (not multi-ply search): winning now > forced block.
        if (WinsWith(r,c,player)) return 10_000_000.0;
        if (WinsWith(r,c,opponent)) return 5_000_000.0;
        int dist = Math.Abs(r - 7) + Math.Abs(c - 7);
        double center = 50.0 * Math.Max(0, (3 - dist) / 3.0);
        int nearby = 0;
        for (int rr = Math.Max(0, r - 2); rr < Math.Min(Size, r + 3); rr++)
        for (int cc = Math.Max(0, c - 2); cc < Math.Min(Size, c + 3); cc++)
            if ((rr != r || cc != c) && Cells[rr, cc] == player) nearby++;
        double structure = nearby >= 2 ? 100 * nearby : 0;
        double newFront = moveCount >= 8 && moveCount < 30 && dist > 5 && nearby <= 1 ? 80 : 0;
        double offense = 0, defense = 0;
        foreach (var (dr, dc) in Directions)
        {
            var own = LineShape(r, c, player, dr, dc);
            var opp = LineShape(r, c, opponent, dr, dc);
            offense += PatternScore(own.count, own.ends);
            defense += PatternScore(opp.count, opp.ends) * .9;
        }
        if (moveCount >= 30) return Math.Max(offense, defense * 1.2);
        if (moveCount >= 10) return Math.Max(offense, defense * 1.1) + center + structure;
        return offense * 1.2 + defense + center + structure + newFront;
    }

    private bool WinsWith(int r, int c, int color)
    {
        if (Cells[r,c]!=0) return false;
        foreach (var (dr,dc) in Directions)
        {
            int total=1;
            foreach (int sign in new[] {-1,1})
                for (int k=1;k<5;k++)
                {
                    int rr=r+sign*k*dr, cc=c+sign*k*dc;
                    if (!Inside(rr,cc) || Cells[rr,cc]!=color) break;
                    total++;
                }
            if (total>=5) return true;
        }
        return false;
    }

    private (int count, int ends) LineShape(int r, int c, int player, int dr, int dc)
    {
        int total = 1, ends = 0;
        foreach (int sign in new[] { 1, -1 })
        {
            int run = 0;
            while (true)
            {
                int rr = r + sign * (run + 1) * dr;
                int cc = c + sign * (run + 1) * dc;
                if (!Inside(rr, cc) || Cells[rr, cc] != player) break;
                run++;
            }
            total += run;
            int openR = r + sign * (run + 1) * dr;
            int openC = c + sign * (run + 1) * dc;
            if (Inside(openR, openC) && Cells[openR, openC] == 0) ends++;
        }
        return (total, ends);
    }

    private static int PatternScore(int count, int ends) => count switch
    {
        >= 5 => 1_000_000,
        4 => ends > 0 ? 100_000 : 5_000,
        3 => ends == 2 ? 10_000 : ends == 1 ? 5_000 : 0,
        2 => ends == 2 ? 1_000 : ends == 1 ? 500 : 0,
        _ => 0
    };

    private static bool Inside(int r, int c) => r >= 0 && r < Size && c >= 0 && c < Size;
}
