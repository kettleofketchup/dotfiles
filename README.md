# dotfiles

Managed with [GNU Stow](https://www.gnu.org/software/stow/). Files symlink into `$HOME`.

## Layout

- Repo root — common config stowed on every machine (`.zshrc`, `.config/`, `.tmux.conf`, etc.)
- `homepc/` — host-specific package, only stowed on the home desktop
  - PipeWire RNNoise filter-chain bound to the SteelSeries Arctis Nova Pro Wireless mic

## Install

```bash
git clone <this-repo> ~/dotfiles
cd ~/dotfiles

# common config (every machine)
stow .

# host-specific packages — only on the matching machine
stow -t ~ homepc        # SteelSeries Arctis denoise filter-chain
```

Re-stow after edits to refresh symlinks:

```bash
stow -R .               # refresh common
stow -R -t ~ homepc     # refresh host package
```

## homepc — Arctis noise cancelling

Provides a virtual PipeWire source `arctis_denoise_source` ("Arctis Noise Cancelling")
that wraps `alsa_input.usb-SteelSeries_Arctis_Nova_Pro_Wireless-00.mono-fallback`
through the RNNoise LADSPA plugin.

**Requirements** (Arch):

```bash
sudo pacman -S noise-suppression-for-voice
```

**After stowing**, restart PipeWire:

```bash
systemctl --user restart pipewire pipewire-pulse wireplumber
```

Then in pavucontrol → Recording, set apps to use **Arctis Noise Cancelling**.

**Tuning:** edit `homepc/.config/pipewire/pipewire.conf.d/99-arctis-denoise.conf`
and tweak `VAD Threshold (%)` (50 default; raise for noisier rooms, lower if soft
speech is being clipped).

**Do not stow `homepc` on other machines** — `target.object` won't match,
the virtual source loads but produces no audio. The `homepc` directory is listed
in `.stow-local-ignore` so `stow .` won't accidentally symlink it as `~/homepc`.
