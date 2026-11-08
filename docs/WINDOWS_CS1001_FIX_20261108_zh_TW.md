# Windows WPF 編譯診斷：CS1001

- User-supplied build log: Windows 10, .NET SDK 10.0.403, project V0.2.2.
- NuGet restore completed; Release build failed with `error CS1001` twice in `VisionDetector.cs` line 196 at columns 35 and 39.
- Cause: malformed C# numeric tokens in `double[] scores = [-1.,-1.];`.
- Fix: `double[] scores = new double[] { -1.0, -1.0 };` in V0.2.3.
- Scope: compiler syntax only. No changes to threshold scores or historical results.
- Verification: source assertion and Python tests in this package; no Windows dotnet compiler in this delivery environment. Windows WPF build must still pass on user's computer.
- Run: `scripts\Verify-WPF-Build-Windows.bat`, then if successful `scripts\Launch-Desktop-Windows.bat`.
- Do not confuse the offline HTML replay viewer with a successful WPF launch.
