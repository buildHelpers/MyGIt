using System;

using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Media;

namespace SourceGit.Views
{
    public partial class Launcher : ChromelessWindow
    {
        public static readonly DirectProperty<Launcher, GridLength> CaptionHeightProperty =
            AvaloniaProperty.RegisterDirect<Launcher, GridLength>(
                nameof(CaptionHeight),
                static o => o.CaptionHeight);

        public GridLength CaptionHeight
        {
            get => _captionHeight;
            set => SetAndRaise(CaptionHeightProperty, ref _captionHeight, value);
        }

        public bool HasRightCaptionButton
        {
            get
            {
                if (OperatingSystem.IsLinux())
                    return !Native.OS.UseSystemWindowFrame;

                return OperatingSystem.IsWindows();
            }
        }

        public Launcher()
        {
            if (OperatingSystem.IsMacOS())
                CaptionHeight = new GridLength(34);
            else if (UseSystemWindowFrame)
                CaptionHeight = new GridLength(30);
            else
                CaptionHeight = new GridLength(38);

            InitializeComponent();
            PositionChanged += OnPositionChanged;

            var layout = ViewModels.Preferences.Instance.Layout;
            Width = layout.LauncherWidth;
            Height = layout.LauncherHeight;

            var x = layout.LauncherPositionX;
            var y = layout.LauncherPositionY;
            if (x != int.MinValue && y != int.MinValue && Screens is { } screens)
            {
                var position = new PixelPoint(x, y);
                var size = new PixelSize((int)layout.LauncherWidth, (int)layout.LauncherHeight);
                var desiredRect = new PixelRect(position, size);
                for (var i = 0; i < screens.ScreenCount; i++)
                {
                    var screen = screens.All[i];
                    if (screen.WorkingArea.Contains(desiredRect))
                    {
                        Position = position;
                        return;
                    }
                }
            }

            WindowStartupLocation = WindowStartupLocation.CenterScreen;
        }

        public void BringToTop()
        {
            if (WindowState == WindowState.Minimized)
                WindowState = _lastWindowState;
            else
                Activate();
        }

        protected override void OnOpened(EventArgs e)
        {
            base.OnOpened(e);

            var preferences = ViewModels.Preferences.Instance;
            WindowState = preferences.Layout.LauncherWindowState;
        }

        protected override void OnPropertyChanged(AvaloniaPropertyChangedEventArgs change)
        {
            base.OnPropertyChanged(change);

            if (change.Property == WindowStateProperty)
            {
                var state = (WindowState)change.NewValue!;
                _lastWindowState = (WindowState)change.OldValue!;

                if (!OperatingSystem.IsMacOS() && !UseSystemWindowFrame)
                    CaptionHeight = new GridLength(state == WindowState.Maximized ? 30 : 38);

                ViewModels.Preferences.Instance.Layout.LauncherWindowState = state;
            }
            else if (change.Property == IsActiveProperty)
            {
                if (!IsActive && DataContext is ViewModels.Launcher { CommandPalette: { } } vm)
                    vm.CommandPalette = null;
            }

            if (OperatingSystem.IsMacOS() && WindowState != WindowState.FullScreen)
            {
                if (change.Property == WindowStateProperty ||
                    change.Property == BoundsProperty ||
                    change.Property == TitleProperty)
                    Native.MacOSUtilities.AdjustTrafficLightsForThickTitleBar(this);
            }
        }

        protected override void OnSizeChanged(SizeChangedEventArgs e)
        {
            base.OnSizeChanged(e);

            if (WindowState == WindowState.Normal)
            {
                var layout = ViewModels.Preferences.Instance.Layout;
                layout.LauncherWidth = Width;
                layout.LauncherHeight = Height;
            }
        }

        protected override async void OnKeyDown(KeyEventArgs e)
        {
            if (DataContext is not ViewModels.Launcher vm)
                return;

            // Check for AltGr (which is detected as Ctrl+Alt)
            bool isAltGr = e.KeyModifiers.HasFlag(KeyModifiers.Control) &&
                           e.KeyModifiers.HasFlag(KeyModifiers.Alt);

            // Skip hotkey processing if AltGr is pressed
            if (isAltGr)
            {
                base.OnKeyDown(e);
                return;
            }

            // Register hotkeys for Windows/Linux (macOS has registered these keys in system menu bar)
            var isMacOS = OperatingSystem.IsMacOS();
            var cmdKey = isMacOS ? KeyModifiers.Meta : KeyModifiers.Control;
            if (!isMacOS)
            {
                if (e is { KeyModifiers: KeyModifiers.Control, Key: Key.OemComma })
                {
                    await this.ShowDialogAsync(new Preferences());
                    e.Handled = true;
                    return;
                }

                if (e is { KeyModifiers: KeyModifiers.None, Key: Key.F1 })
                {
                    await this.ShowDialogAsync(new Hotkeys());
                    e.Handled = true;
                    return;
                }

                if (e is { KeyModifiers: KeyModifiers.Control, Key: Key.Q })
                {
                    App.Quit(0);
                    return;
                }
            }

            // Ctrl+` to open terminal. On macOS, Cmd+` is used to switch between windows
            if (e is { Key: Key.OemTilde, KeyModifiers: KeyModifiers.Control })
            {
                if (vm.ActivePage.Data is ViewModels.Repository repo)
                    Native.OS.OpenTerminal(repo.FullPath);
                else
                    ViewModels.Welcome.Instance.OpenTerminal();

                e.Handled = true;
                return;
            }

            if (vm.CommandPalette != null)
            {
                if (e.Key == Key.Escape)
                {
                    vm.CommandPalette = null;
                    e.Handled = true;
                }
                else if (vm.ActivePage.Data is ViewModels.Repository repo
                    && vm.CommandPalette is ViewModels.LauncherPagesCommandPalette
                    && e.Key == Key.P
                    && e.KeyModifiers == (cmdKey | KeyModifiers.Shift))
                {
                    vm.CommandPalette = new ViewModels.RepositoryCommandPalette(repo);
                    e.Handled = true;
                }

                return;
            }

            if (e.KeyModifiers.HasFlag(cmdKey))
            {
                if (e.Key == Key.W)
                {
                    vm.CloseTab(null);
                    e.Handled = true;
                    return;
                }

                if (e.Key == Key.R)
                {
                    if (vm.ActivePage.Data is not ViewModels.Welcome)
                        vm.AddNewTab();

                    ViewModels.Welcome.Instance.Clone();
                    e.Handled = true;
                    return;
                }

                if (e.Key == Key.L)
                {
                    if (vm.ActivePage.Data is not ViewModels.Welcome)
                        vm.AddNewTab();

                    ViewModels.Welcome.Instance.OpenLocalRepository();
                    e.Handled = true;
                    return;
                }

                if (e.Key == Key.T && e.KeyModifiers == cmdKey)
                {
                    vm.AddNewTab();
                    e.Handled = true;
                    return;
                }

                if ((isMacOS && e.KeyModifiers.HasFlag(KeyModifiers.Alt) && e.Key == Key.Right) ||
                    (!isMacOS && !e.KeyModifiers.HasFlag(KeyModifiers.Shift) && e.Key == Key.Tab))
                {
                    vm.GotoNextTab();
                    e.Handled = true;
                    return;
                }

                if ((isMacOS && e.KeyModifiers.HasFlag(KeyModifiers.Alt) && e.Key == Key.Left) ||
                    (!isMacOS && e.KeyModifiers.HasFlag(KeyModifiers.Shift) && e.Key == Key.Tab))
                {
                    vm.GotoPrevTab();
                    e.Handled = true;
                    return;
                }

                if (vm.ActivePage.Data is ViewModels.Repository repo)
                {
                    switch (e.Key)
                    {
                        case Key.D1 or Key.NumPad1:
                            repo.SelectedViewIndex = 0;
                            e.Handled = true;
                            return;
                        case Key.D2 or Key.NumPad2:
                            repo.SelectedViewIndex = 1;
                            e.Handled = true;
                            return;
                        case Key.D3 or Key.NumPad3:
                            repo.SelectedViewIndex = 2;
                            e.Handled = true;
                            return;
                        case Key.P when e.KeyModifiers.HasFlag(KeyModifiers.Shift):
                            vm.CommandPalette = new ViewModels.RepositoryCommandPalette(repo);
                            e.Handled = true;
                            return;
                        case Key.F when e.KeyModifiers.HasFlag(KeyModifiers.Shift):
                            repo.Histories.IsSearchingCommits = !repo.Histories.IsSearchingCommits;
                            e.Handled = true;
                            return;
                        case Key.B when e.KeyModifiers.HasFlag(KeyModifiers.Shift):
                            if (repo.CanCreatePopup() && repo.GetSelectedCommitInHistory() is { } bc)
                                repo.ShowPopup(new ViewModels.CreateBranch(repo, bc));
                            e.Handled = true;
                            return;
                        case Key.T when e.KeyModifiers.HasFlag(KeyModifiers.Shift):
                            if (repo.CanCreatePopup() && repo.GetSelectedCommitInHistory() is { } tc)
                                repo.ShowPopup(new ViewModels.CreateTag(repo, tc));
                            e.Handled = true;
                            return;
                        case Key.E:
                            Native.OS.OpenInFileManager(repo.FullPath);
                            e.Handled = true;
                            return;
                    }
                }
            }
            else if (e.Key == Key.Escape)
            {
                vm.ActivePage.CancelPopup();
                vm.ActivePage.Notifications.Clear();
                e.Handled = true;
                return;
            }
            else if (e.Key == Key.F5)
            {
                if (vm.ActivePage.Data is ViewModels.Repository repo)
                {
                    repo.RefreshAll();
                    e.Handled = true;
                    return;
                }
                else if (vm.ActivePage.Data is ViewModels.Welcome welcome)
                {
                    e.Handled = true;
                    await welcome.UpdateStatusAsync(true, null);
                    return;
                }
            }

            base.OnKeyDown(e);
        }

        protected override void OnPointerPressed(PointerPressedEventArgs e)
        {
            base.OnPointerPressed(e);

            if (!e.Handled)
            {
                if (e.Properties.PointerUpdateKind == PointerUpdateKind.XButton1Pressed)
                    (DataContext as ViewModels.Launcher)?.GotoPrevTab();
                else if (e.Properties.PointerUpdateKind == PointerUpdateKind.XButton2Pressed)
                    (DataContext as ViewModels.Launcher)?.GotoNextTab();
            }
        }

        protected override void OnClosing(WindowClosingEventArgs e)
        {
            base.OnClosing(e);

            if (!Design.IsDesignMode && DataContext is ViewModels.Launcher launcher)
                launcher.CloseAll();
        }

        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);

            if (!Design.IsDesignMode)
                ViewModels.Preferences.Instance.Save();

            App.Quit(0);
        }

        private void OnPositionChanged(object sender, PixelPointEventArgs e)
        {
            if (WindowState == WindowState.Normal)
            {
                var layout = ViewModels.Preferences.Instance.Layout;
                layout.LauncherPositionX = Position.X;
                layout.LauncherPositionY = Position.Y;
            }
        }

        // The home button remains available regardless of the selected repository tab.
        private void OnShowWorkspaceHome(object sender, RoutedEventArgs e)
        {
            if (DataContext is ViewModels.Launcher launcher)
                launcher.ShowWorkspaceHome();

            e.Handled = true;
        }

        private void OnOpenWorkspaceMenu(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && DataContext is ViewModels.Launcher launcher)
            {
                launcher.CommandPalette = null;

                var pref = ViewModels.Preferences.Instance;
                var menu = new ContextMenu
                {
                    Placement = PlacementMode.BottomEdgeAlignedLeft,
                    VerticalOffset = -6,
                };

                // One click to return home, keeping every open repository tab intact.
                var home = new MenuItem
                {
                    Header = App.Text("PageTabBar.Welcome.Title"),
                    Icon = this.CreateMenuIcon("Icons.Workspace"),
                };
                home.Click += (_, ev) =>
                {
                    launcher.ShowWorkspaceHome();
                    ev.Handled = true;
                };
                menu.Items.Add(home);
                menu.Items.Add(new MenuItem { Header = "-" });

                menu.Items.Add(new MenuItem
                {
                    Header = new TextBlock
                    {
                        Text = App.Text("Launcher.Workspaces"),
                        FontWeight = FontWeight.Bold,
                    },
                    IsEnabled = false,
                });

                foreach (var workspace in pref.Workspaces)
                {
                    var icon = this.CreateMenuIcon(workspace.IsActive ? "Icons.Check" : "Icons.Workspace");
                    icon.Fill = workspace.Brush;

                    var item = new MenuItem { Header = workspace.Name, Icon = icon };
                    item.Click += (_, ev) =>
                    {
                        if (!workspace.IsActive)
                            launcher.SwitchWorkspace(workspace);
                        else
                            launcher.ShowWorkspaceHome();

                        ev.Handled = true;
                    };
                    menu.Items.Add(item);
                }

                // Switching an opened repository only selects its existing page.
                // It never checks out a branch, reloads a repository or discards changes.
                menu.Items.Add(new MenuItem { Header = "-" });
                menu.Items.Add(new MenuItem
                {
                    Header = new TextBlock
                    {
                        Text = App.Text("Launcher.Pages"),
                        FontWeight = FontWeight.Bold,
                    },
                    IsEnabled = false,
                });

                foreach (var page in launcher.Pages)
                {
                    if (page.Data is not ViewModels.Repository)
                        continue;

                    var icon = this.CreateMenuIcon(page == launcher.ActivePage ? "Icons.Check" : "Icons.Repositories");
                    var item = new MenuItem { Header = page.Node.Name, Icon = icon };
                    item.Click += (_, ev) =>
                    {
                        launcher.ActivePage = page;
                        ev.Handled = true;
                    };
                    menu.Items.Add(item);
                }

                // The existing searchable palette also includes managed, not-yet-opened repos.
                var search = new MenuItem
                {
                    Header = App.Text("Welcome.Search"),
                    Icon = this.CreateMenuIcon("Icons.Search"),
                };
                search.Click += (_, ev) =>
                {
                    launcher.CommandPalette = new ViewModels.LauncherPagesCommandPalette(launcher);
                    ev.Handled = true;
                };
                menu.Items.Add(search);
                menu.Items.Add(new MenuItem { Header = "-" });

                var configure = new MenuItem { Header = App.Text("Workspace.Configure") };
                configure.Click += async (_, ev) =>
                {
                    await this.ShowDialogAsync(new ViewModels.ConfigureWorkspace());
                    ev.Handled = true;
                };
                menu.Items.Add(configure);
                menu.Open(btn);
            }

            e.Handled = true;
        }

        private void OnOpenPagesCommandPalette(object sender, RoutedEventArgs e)
        {
            if (DataContext is ViewModels.Launcher vm)
                vm.CommandPalette = new ViewModels.LauncherPagesCommandPalette(vm);
            e.Handled = true;
        }

        private void OnCloseCommandPalette(object sender, PointerPressedEventArgs e)
        {
            if (e.Source == sender && DataContext is ViewModels.Launcher vm)
                vm.CommandPalette = null;
            e.Handled = true;
        }

        private async void OnShowNewVersion(object sender, RoutedEventArgs e)
        {
            if (DataContext is ViewModels.Launcher { NewVersion: { } ver } vm)
            {
                vm.NewVersion = null;

                var ctx = new ViewModels.SelfUpdate { Data = ver };
                var dialog = new SelfUpdate() { DataContext = ctx };
                await dialog.ShowDialog(this);
            }

            e.Handled = true;
        }

        private GridLength _captionHeight = new(32);
        private WindowState _lastWindowState = WindowState.Normal;
    }
}

