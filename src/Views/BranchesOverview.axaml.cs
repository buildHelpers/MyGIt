using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Interactivity;

namespace SourceGit.Views
{
    /// <summary>
    /// Branch management surface. Delegates all Git operations to the existing
    /// Repository view model and SourceGit popup classes.
    /// </summary>
    public partial class BranchesOverview : UserControl
    {
        public BranchesOverview()
        {
            InitializeComponent();
        }

        private void OnRefreshRepository(object sender, RoutedEventArgs e)
        {
            if (DataContext is ViewModels.Repository repository)
                repository.RefreshAll();

            e.Handled = true;
        }

        private void OnAddWorktree(object sender, RoutedEventArgs e)
        {
            if (DataContext is ViewModels.Repository repository && repository.CanCreatePopup())
                repository.AddWorktree();

            e.Handled = true;
        }

        private void OnViewCurrentHead(object sender, RoutedEventArgs e)
        {
            if (DataContext is ViewModels.Repository repository && repository.CurrentBranch is { } branch)
            {
                repository.SelectedViewIndex = 0;
                repository.NavigateToCommit(branch.Head);
            }

            e.Handled = true;
        }

        private void OnBranchDoubleTapped(object sender, TappedEventArgs e)
        {
            if (DataContext is ViewModels.Repository repository &&
                repository.CanCreatePopup() &&
                sender is Grid { DataContext: Models.Branch branch } &&
                branch is { IsLocal: true, IsCurrent: false, HasWorktree: false })
            {
                repository.ShowPopup(new ViewModels.Checkout(repository, branch));
                e.Handled = true;
            }
        }

        private void OnOpenWorktree(object sender, RoutedEventArgs e)
        {
            if (sender is Button { DataContext: ViewModels.Worktree tree })
            {
                App.GetLauncher().OpenRepositoryInTab(tree.FullPath, null);
                e.Handled = true;
            }
        }

        private void OnWorktreeDoubleTapped(object sender, TappedEventArgs e)
        {
            if (sender is Border { DataContext: ViewModels.Worktree tree })
            {
                App.GetLauncher().OpenRepositoryInTab(tree.FullPath, null);
                e.Handled = true;
            }
        }
    }
}
