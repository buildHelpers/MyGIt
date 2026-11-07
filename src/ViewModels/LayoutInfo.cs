using Avalonia.Controls;
using CommunityToolkit.Mvvm.ComponentModel;

namespace SourceGit.ViewModels
{
    public class LayoutInfo : ObservableObject
    {
        public double LauncherWidth
        {
            get;
            set;
        } = 1360;

        public double LauncherHeight
        {
            get;
            set;
        } = 820;

        public int LauncherPositionX
        {
            get;
            set;
        } = int.MinValue;

        public int LauncherPositionY
        {
            get;
            set;
        } = int.MinValue;

        public WindowState LauncherWindowState
        {
            get;
            set;
        } = WindowState.Normal;

        public double RepositorySidebarWidth
        {
            get;
            set;
        } = 230;

        public double RepositorySearchCommitWidth
        {
            get;
            set;
        } = 250;

        public bool IsSidebarCollapsedInLocalChanges
        {
            get => _isSidebarCollapsedInLocalChanges;
            set => SetProperty(ref _isSidebarCollapsedInLocalChanges, value);
        }

        public GridLength WorkingCopyLeftWidth
        {
            get => _workingCopyLeftWidth;
            set => SetProperty(ref _workingCopyLeftWidth, value);
        }

        public GridLength StashesLeftWidth
        {
            get => _stashesLeftWidth;
            set => SetProperty(ref _stashesLeftWidth, value);
        }

        public GridLength CommitDetailChangesLeftWidth
        {
            get => _commitDetailChangesLeftWidth;
            set => SetProperty(ref _commitDetailChangesLeftWidth, value);
        }

        public GridLength CommitDetailFilesLeftWidth
        {
            get => _commitDetailFilesLeftWidth;
            set => SetProperty(ref _commitDetailFilesLeftWidth, value);
        }

        private GridLength _workingCopyLeftWidth = new GridLength(280, GridUnitType.Pixel);
        private GridLength _stashesLeftWidth = new GridLength(300, GridUnitType.Pixel);
        private GridLength _commitDetailChangesLeftWidth = new GridLength(256, GridUnitType.Pixel);
        private GridLength _commitDetailFilesLeftWidth = new GridLength(256, GridUnitType.Pixel);
        private bool _isSidebarCollapsedInLocalChanges = true;
    }
}
