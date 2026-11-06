using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

using CommunityToolkit.Mvvm.ComponentModel;

namespace SourceGit.ViewModels
{
    /// <summary>
    /// A local repository destination, not a Git operation.
    /// </summary>
    public sealed class QuickRepositoryItem
    {
        public string Name { get; init; } = string.Empty;
        public string Path { get; init; } = string.Empty;
        public bool IsRecent { get; set; }
        public bool IsOpen { get; set; }
    }

    /// <summary>
    /// Searchable repository switcher shown directly beneath the global title bar.
    /// Merges recently used paths, managed repositories, restored workspaces and open tabs.
    /// </summary>
    public sealed class QuickRepositorySwitcher : ObservableObject
    {
        public List<QuickRepositoryItem> VisibleRepositories
        {
            get => _visibleRepositories;
            private set
            {
                if (SetProperty(ref _visibleRepositories, value))
                    OnPropertyChanged(nameof(HasMatches));
            }
        }

        public bool HasMatches => _visibleRepositories.Count > 0;

        public QuickRepositoryItem SelectedRepository
        {
            get => _selectedRepository;
            set => SetProperty(ref _selectedRepository, value);
        }

        public string SearchFilter
        {
            get => _searchFilter;
            set
            {
                if (SetProperty(ref _searchFilter, value))
                    UpdateVisible();
            }
        }

        public QuickRepositorySwitcher(Launcher launcher)
        {
            _launcher = launcher;
            Refresh();
        }

        /// <summary>
        /// Open the selected repository using the existing validated SourceGit path.
        /// If it is already open, the Launcher simply selects its existing page.
        /// </summary>
        public bool Open(QuickRepositoryItem item)
        {
            if (item == null)
                return false;

            _launcher.OpenRepositoryInTab(item.Path, null);
            if (_launcher.ActivePage is not { Data: Repository active } ||
                !_pathComparer.Equals(Normalize(active.FullPath), Normalize(item.Path)))
                return false;

            // Also handles choosing the already-selected tab (no property-change event).
            Preferences.Instance.RememberRepository(active.FullPath);
            return true;
        }

        private void Refresh()
        {
            var preferences = Preferences.Instance;
            var all = new Dictionary<string, QuickRepositoryItem>(_pathComparer);

            CollectManaged(all, preferences.RepositoryNodes);

            foreach (var workspace in preferences.Workspaces)
            {
                foreach (var repo in workspace.Repositories)
                    Add(all, repo, null, false);
            }

            foreach (var page in _launcher.Pages)
            {
                if (page.Data is Repository repo)
                    Add(all, repo.FullPath, page.Node.Name, true);
            }

            var recentPaths = preferences.RecentRepositories ?? [];
            foreach (var path in recentPaths)
                Add(all, path, null, false);

            // First run after upgrading: show the restored opened repositories as recent.
            var recent = new List<string>(recentPaths);
            if (recent.Count == 0)
            {
                foreach (var page in _launcher.Pages.Reverse())
                {
                    if (page.Data is Repository repo)
                        recent.Add(repo.FullPath);
                }
            }

            var ordered = new List<QuickRepositoryItem>();
            var seen = new HashSet<string>(_pathComparer);

            foreach (var path in recent)
            {
                var normalized = Normalize(path);
                if (all.TryGetValue(normalized, out var item) && seen.Add(normalized))
                {
                    item.IsRecent = true;
                    ordered.Add(item);
                }
            }

            foreach (var item in all.Values
                         .Where(item => !seen.Contains(item.Path))
                         .OrderByDescending(item => item.IsOpen)
                         .ThenBy(item => item.Name, StringComparer.OrdinalIgnoreCase)
                         .ThenBy(item => item.Path, StringComparer.OrdinalIgnoreCase))
                ordered.Add(item);

            _allRepositories = ordered;
            UpdateVisible();
        }

        private void UpdateVisible()
        {
            var filter = _searchFilter?.Trim();
            var items = string.IsNullOrEmpty(filter)
                ? _allRepositories
                : _allRepositories.Where(item =>
                    item.Name.Contains(filter, StringComparison.OrdinalIgnoreCase) ||
                    item.Path.Contains(filter, StringComparison.OrdinalIgnoreCase)).ToList();

            VisibleRepositories = items;
            SelectedRepository = items.Count > 0 ? items[0] : null;
        }

        private static void CollectManaged(
            Dictionary<string, QuickRepositoryItem> all,
            List<RepositoryNode> nodes)
        {
            foreach (var node in nodes)
            {
                if (node.IsRepository)
                    Add(all, node.Id, node.Name, false);
                else
                    CollectManaged(all, node.SubNodes);
            }
        }

        private static void Add(
            Dictionary<string, QuickRepositoryItem> all,
            string path,
            string name,
            bool isOpen)
        {
            var normalized = Normalize(path);
            if (string.IsNullOrEmpty(normalized))
                return;

            if (all.TryGetValue(normalized, out var existing))
            {
                existing.IsOpen |= isOpen;
                return;
            }

            all.Add(normalized, new QuickRepositoryItem
            {
                Name = !string.IsNullOrWhiteSpace(name)
                    ? name
                    : System.IO.Path.GetFileName(normalized),
                Path = normalized,
                IsOpen = isOpen,
            });
        }

        private static string Normalize(string path)
        {
            return path?.Replace('\\', '/').TrimEnd('/') ?? string.Empty;
        }

        private static readonly StringComparer _pathComparer =
            OperatingSystem.IsWindows() ? StringComparer.OrdinalIgnoreCase : StringComparer.Ordinal;

        private readonly Launcher _launcher;
        private List<QuickRepositoryItem> _allRepositories = [];
        private List<QuickRepositoryItem> _visibleRepositories = [];
        private QuickRepositoryItem _selectedRepository = null;
        private string _searchFilter = string.Empty;
    }
}
