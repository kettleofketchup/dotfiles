-- Learn how to configure Hyprland: https://wiki.hypr.land/Configuring/Start/

-- Omarchy's bootstrap keeps path setup out of this user config.
dofile((os.getenv("OMARCHY_PATH") or "/usr/share/omarchy") .. "/default/hypr/bootstrap.lua")

-- Disable all Omarchy default bindings. Add your own in hypr/bindings.lua.
-- omarchy_default_bindings = false
--
-- Or disable only bindings for Omarchy's preinstalled apps/web apps while
-- keeping core window-manager bindings:
-- omarchy_preinstalled_bindings = false

-- Load Omarchy defaults.
require("default.hypr.omarchy")

-- Put your personal overrides in these files. They're loaded after Omarchy's
-- defaults so package updates can improve the defaults without rewriting your
-- ~/.config/hypr files.
require("hypr.monitors")
require("hypr.input")
require("hypr.bindings")
require("hypr.looknfeel")
require("hypr.autostart")

-- Toggle config flags dynamically.
require("default.hypr.toggles")

-- Add any other personal Hyprland configuration below.
-- o.window("qemu", { workspace = "5" })

-- Gamepad input is invisible to the compositor: libinput drops joystick devices,
-- so ext-idle-notify never sees the controller and the idle timer runs unchecked
-- while you play. Nothing else rescues it -- org.freedesktop.ScreenSaver has no
-- owner on the session bus, so Steam's own D-Bus inhibit lands nowhere.
--
-- "focus" rather than "fullscreen": a fullscreen rule misses windowed games,
-- Big Picture, and browsing the library with the controller. Omarchy's own
-- steam.lua sets fullscreen on class "steam", which is also float = true and so
-- never fullscreen -- that rule can never fire.
o.window("^steam_app_.*$", { idle_inhibit = "focus" })
o.window("^gamescope$", { idle_inhibit = "focus" })
o.window("^steam$", { idle_inhibit = "focus" })

-- Added by hyprmoncfg: its generated monitor rules load last, so nothing before this can override the applied layout.
do local path = os.getenv("HOME") .. "/.config/hypr/hyprmoncfg-monitors.lua"; local file = io.open(path, "r"); if file then file:close(); dofile(path) end end
