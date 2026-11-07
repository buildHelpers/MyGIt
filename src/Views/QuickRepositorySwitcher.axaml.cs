using System;

using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Interactivity;

namespace SourceGit.Views
{
    public partial class QuickRepositorySwitcher : UserControl
    {
        public event EventHandler CloseRequested;

        public QuickRepositorySwitcher(ViewModels.Launcher launcher)
        {
            InitializeComponent();
            DataContext = new ViewModels.QuickRepositorySwitcher(launcher);
        }

        protected override void OnLoaded(RoutedEventArgs e)
        {
            base.OnLoaded(e);
            SearchBox.Focus(NavigationMethod.Directional);
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            if (DataContext is not ViewModels.QuickRepositorySwitcher vm)
            {
                base.OnKeyDown(e);
                return;
            }

            if (e.Key == Key.Enter)
            {
                TryOpen(vm.SelectedRepository);
                e.Handled = true;
            }
            else if (e.Key == Key.Down && SearchBox.IsKeyboardFocusWithin &&
                     vm.VisibleRepositories.Count > 0)
            {
                RepositoryList.Focus(NavigationMethod.Directional);
                vm.SelectedRepository = vm.VisibleRepositories[0];
                e.Handled = true;
            }
            else if (e.Key == Key.Escape)
            {
                CloseRequested?.Invoke(this, EventArgs.Empty);
                e.Handled = true;
            }

            if (!e.Handled)
                base.OnKeyDown(e);
        }

        private void OnRepositoryTapped(object sender, TappedEventArgs e)
        {
            if (sender is Grid { DataContext: ViewModels.QuickRepositoryItem item })
            {
                TryOpen(item);
                e.Handled = true;
            }
        }

        private void TryOpen(ViewModels.QuickRepositoryItem item)
        {
            if (DataContext is ViewModels.QuickRepositorySwitcher vm && vm.Open(item))
                CloseRequested?.Invoke(this, EventArgs.Empty);
        }
    }
}
