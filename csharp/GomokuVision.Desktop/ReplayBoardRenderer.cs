using System;
using System.Collections.Generic;
using System.Globalization;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace GomokuVision.Desktop;

/// <summary>Renders exactly the selected historical moves. No video or training assets required.</summary>
public static class ReplayBoardRenderer
{
    public static BitmapSource Draw(IReadOnlyList<MoveRow> moves, int count)
    {
        count = Math.Clamp(count, 0, moves.Count);
        var board = new GomokuVision.Board();
        for (int i = 0; i < count; ++i)
        {
            var m = moves[i];
            int color = m.Color.Equals("Black", StringComparison.OrdinalIgnoreCase) ? 1 :
                        m.Color.Equals("White", StringComparison.OrdinalIgnoreCase) ? 2 : 0;
            if (color == 0 || !TryParsePosition(m.Position, out int row, out int col))
                throw new FormatException($"Invalid move #{i + 1}: {m.Color} {m.Position}");
            board.Place(m.Frame, color, row, col); // Also detects occupied / duplicated positions.
        }

        const int size = 440;
        const double start = 38, end = 412, spacing = (end - start) / 14.0;
        var visual = new DrawingVisual();
        using (var dc = visual.RenderOpen())
        {
            dc.DrawRoundedRectangle(new SolidColorBrush(Color.FromRgb(215, 186, 139)), null,
                                    new Rect(0, 0, size, size), 9, 9);
            dc.DrawRoundedRectangle(new SolidColorBrush(Color.FromRgb(230, 201, 154)),
                                    new Pen(new SolidColorBrush(Color.FromRgb(128, 100, 70)), 1.8),
                                    new Rect(10, 10, size - 20, size - 20), 4, 4);
            var gridPen = new Pen(new SolidColorBrush(Color.FromRgb(110, 88, 61)), 1.05);
            for (int k = 0; k < 15; k++)
            {
                var p = start + k * spacing;
                dc.DrawLine(gridPen, new Point(start, p), new Point(end, p));
                dc.DrawLine(gridPen, new Point(p, start), new Point(p, end));
                var column = Label(((char)('A' + k)).ToString(), 12);
                dc.DrawText(column, new Point(p - column.Width / 2, 15));
                var row = Label((k + 1).ToString(CultureInfo.InvariantCulture), 11);
                dc.DrawText(row, new Point(13, p - row.Height / 2));
            }
            var last = count > 0 ? board.Moves[count - 1] : null;
            foreach (var m in board.Moves)
            {
                var center = new Point(start + m.Col * spacing, start + m.Row * spacing);
                var fill = m.Color == 1 ? new SolidColorBrush(Color.FromRgb(35, 38, 42)) : Brushes.WhiteSmoke;
                dc.DrawEllipse(fill, new Pen(new SolidColorBrush(Color.FromRgb(59, 65, 72)), 1.3),
                               center, 9.5, 9.5);
            }
            var win = board.Winner();
            if (win is not null)
            {
                var coords = win.Value.Line;
                if (coords.Count >= 5)
                {
                    var a = new Point(start + coords[0].Col * spacing, start + coords[0].Row * spacing);
                    var b = new Point(start + coords[^1].Col * spacing, start + coords[^1].Row * spacing);
                    dc.DrawLine(new Pen(new SolidColorBrush(Color.FromArgb(215, 220, 35, 45)), 3.5), a, b);
                }
            }
            if (last is not null)
            {
                var highlight = new Point(start + last.Col * spacing, start + last.Row * spacing);
                dc.DrawEllipse(null, new Pen(Brushes.DodgerBlue, 2.7), highlight, 13, 13);
            }
        }
        var bitmap = new RenderTargetBitmap(size, size, 96, 96, PixelFormats.Pbgra32);
        bitmap.Render(visual);
        bitmap.Freeze();
        return bitmap;
    }

    private static bool TryParsePosition(string position, out int row, out int col)
    {
        row = col = -1;
        position = position.Trim().ToUpperInvariant();
        if (position.Length < 2 || position.Length > 3 || position[0] < 'A' || position[0] > 'O')
            return false;
        if (!int.TryParse(position.AsSpan(1), NumberStyles.None, CultureInfo.InvariantCulture, out int number) ||
            number < 1 || number > 15) return false;
        col = position[0] - 'A';
        row = number - 1;
        return true;
    }

    private static FormattedText Label(string text, double fontSize) => new(
        text, CultureInfo.InvariantCulture, FlowDirection.LeftToRight,
        new Typeface("Segoe UI"), fontSize, new SolidColorBrush(Color.FromRgb(72, 58, 45)), 1.0);
}
