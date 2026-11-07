using System;
using System.IO;

namespace SourceGit.Views
{
    /// <summary>
    /// Copies the bundled MyGIt color preset to this application's private
    /// configuration directory. Does not edit the upstream SourceGit settings.
    /// </summary>
    internal static class MyGItThemePresets
    {
        internal static bool TryInstall(string filename, out string targetPath)
        {
            targetPath = null;
            if (filename != "MyGIt-Light.json" && filename != "MyGIt-Dark.json")
                return false;

            try
            {
                using var source = typeof(MyGItThemePresets).Assembly.GetManifestResourceStream(
                    "MyGIt.Themes." + filename);
                if (source == null)
                    throw new FileNotFoundException("Bundled theme resource is missing", filename);

                var directory = Path.Combine(Native.OS.BasicDirectories.ConfigDir, "MyGItThemes");
                Directory.CreateDirectory(directory);

                var output = Path.Combine(directory, filename);
                var temporary = Path.Combine(directory, filename + "." + Guid.NewGuid().ToString("N") + ".tmp");
                try
                {
                    using (var stream = File.Create(temporary))
                        source.CopyTo(stream);

                    File.Move(temporary, output, true);
                }
                finally
                {
                    if (File.Exists(temporary))
                        File.Delete(temporary);
                }

                targetPath = output;
                return true;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine("Unable to install MyGIt appearance preset: " + ex.Message);
                return false;
            }
        }
    }
}
