local icons = require('lib.icons')

return {
  "folke/which-key.nvim",
  event = "VeryLazy",
  opts = {
    preset = 'modern',
    plugins = {
      marks = true,
      registers = true,
      spelling = {
        enabled = true,
        suggestions = 30,
      },
      presets = {
        operators = true,
        motions = true,
        text_objects = true,
        windows = true,
        nav = true,
        z = true,
        g = true,
      },
    },
    icons = {
      breadcrumb = icons.ui.ArrowOpen,
      separator = icons.ui.Arrow,
      group = '',
      keys = {
        Space = icons.ui.Rocket,
      },
      rules = false,
    },
    win = {
      no_overlap = true,
      border = 'rounded',
      width = 0.8,
      height = { min = 5, max = 25 },
      padding = { 1, 2 },
      title = true,
      title_pos = 'center',
      zindex = 1000,
      wo = {
        winblend = 10,
      },
    },
    layout = {
      width = { min = 20 },
      spacing = 6,
      align = 'center',
    },
    show_help = false,
    show_keys = true,
    triggers = {
      { '<auto>', mode = 'nvisoct' },
      { '<leader>', mode = { 'n', 'v' } },
    },
  },
  config = function(_, opts)
    local which_key = require('which-key')
    which_key.setup(opts)

    -- Normal mode mappings
    which_key.add({
      mode = 'n',
      { '<leader>x', ':x<cr>', desc = ' Save and Quit' },

      -- Code
      { '<leader>c', group = ' Code' },
      { '<leader>cF', ':retab<cr>', desc = 'Fix Tabs' },
      { '<leader>cR', ':ReloadConfig<cr>', desc = 'Reload Configs' },
      { '<leader>cd', ':RootDir<cr>', desc = 'Root Directory' },
      { '<leader>cf', ':lua vim.lsp.buf.format({async = true})<cr>', desc = 'Format File' },
      { '<leader>cl', '::g/^\\s*$/d<cr>', desc = 'Clean Empty Lines' },
      { '<leader>co', ':Dashboard<cr>', desc = 'Dashboard' },
      { '<leader>cs', ':source %<cr>', desc = 'Source File' },

      -- Edit
      { '<leader>e', group = ' Edit' },
      { '<leader>ea', ':b#<cr>', desc = 'Alternate File' },
      { '<leader>ec', group = 'Edit Configs' },
      { '<leader>ecn', ':e $MYVIMRC<cr>', desc = 'Neovim Init' },
      { '<leader>em', ':e README.md<cr>', desc = 'Readme' },
      { '<leader>en', ':enew<cr>', desc = 'New File' },

      -- Find (using snacks picker)
      { '<leader>f', group = ' Find' },
      { '<leader>fb', ':lua Snacks.picker.buffers()<cr>', desc = 'Buffers' },
      { '<leader>fc', ':lua Snacks.picker.command_history()<cr>', desc = 'Command History' },
      { '<leader>fC', ':lua Snacks.picker.commands()<cr>', desc = 'Commands' },
      { '<leader>ff', ':lua Snacks.picker.files()<cr>', desc = 'Files' },
      { '<leader>fg', ':lua Snacks.picker.git_files()<cr>', desc = 'Git Files' },
      { '<leader>fh', ':lua Snacks.picker.help()<cr>', desc = 'Help Tags' },
      { '<leader>fk', ':lua Snacks.picker.keymaps()<cr>', desc = 'Keymaps' },
      { '<leader>fl', ':lua Snacks.picker.lsp_symbols()<cr>', desc = 'LSP Symbols' },
      { '<leader>fm', ':lua Snacks.picker.man()<cr>', desc = 'Man Pages' },
      { '<leader>fn', ':lua Snacks.picker.notifications()<cr>', desc = 'Notifications' },
      { '<leader>fr', ':lua Snacks.picker.recent()<cr>', desc = 'Recent Files' },
      { '<leader>fs', ':lua Snacks.picker.smart()<cr>', desc = 'Smart' },
      { '<leader>fw', ':lua Snacks.picker.grep_word()<cr>', desc = 'Grep Word' },
      { '<leader>fx', ':%bd|e#|bd#<cr>', desc = 'Close except current' },
      { '<leader>/', ':lua Snacks.picker.grep()<cr>', desc = 'Live Grep' },

      -- Git
      { '<leader>g', group = ' Git' },
      { '<leader>gb', ":lua require('gitsigns').blame_line({full = true})<cr>", desc = 'Blame' },
      { '<leader>gd', ':Gitsigns diffthis HEAD<cr>', desc = 'Git Diff' },
      { '<leader>gg', ':lua require("snacks").lazygit()<cr>', desc = 'Lazygit' },
      { '<leader>gi', ':Gitsigns preview_hunk<cr>', desc = 'Hunk Info' },
      { '<leader>gj', ':Gitsigns next_hunk<cr>', desc = 'Next Hunk' },
      { '<leader>gk', ':Gitsigns prev_hunk<cr>', desc = 'Prev Hunk' },
      { '<leader>gr', ':Gitsigns reset_hunk<cr>', desc = 'Reset Hunk' },
      { '<leader>gs', ':Gitsigns stage_hunk<cr>', desc = 'Stage Hunk' },
      { '<leader>gu', ':Gitsigns undo_stage_hunk<cr>', desc = 'Undo Stage Hunk' },

      -- LSP
      { '<leader>l', group = ' LSP' },
      { '<leader>la', ':lua vim.lsp.buf.code_action()<cr>', desc = 'Code Action' },
      { '<leader>ld', ':lua vim.lsp.buf.definition()<cr>', desc = 'Goto Definition' },
      { '<leader>lf', ':lua vim.lsp.buf.references()<cr>', desc = 'References' },
      { '<leader>lh', ':lua vim.lsp.buf.hover()<cr>', desc = 'Hover' },
      { '<leader>lI', ':LspInfo<cr>', desc = 'LSP Info' },
      { '<leader>li', ':lua vim.lsp.buf.implementation()<cr>', desc = 'Implementation' },
      { '<leader>lr', ':lua vim.lsp.buf.rename()<cr>', desc = 'Rename' },
      { '<leader>ls', ':lua vim.lsp.buf.signature_help()<cr>', desc = 'Signature Help' },
      { '<leader>lt', ':lua vim.lsp.buf.type_definition()<cr>', desc = 'Type Definition' },

      -- Notes/Scratch
      { '<leader>n', group = ' Notes' },
      { '<leader>nn', ':lua Snacks.scratch()<cr>', desc = 'New Scratch' },
      { '<leader>ns', ':lua Snacks.scratch.select()<cr>', desc = 'Select Scratch' },

      -- Options
      { '<leader>o', group = ' Options' },
      { '<leader>on', ':set number!<cr>', desc = 'Line Numbers' },
      { '<leader>or', ':set relativenumber!<cr>', desc = 'Relative Numbers' },

      -- Packages
      { '<leader>p', group = ' Packages' },
      { '<leader>pc', ':Lazy check<cr>', desc = 'Check' },
      { '<leader>pi', ':Lazy install<cr>', desc = 'Install' },
      { '<leader>pl', ':Lazy log<cr>', desc = 'Log' },
      { '<leader>pm', ':Mason<cr>', desc = 'Mason' },
      { '<leader>pp', ':Lazy<cr>', desc = 'Plugins' },
      { '<leader>ps', ':Lazy sync<cr>', desc = 'Sync' },
      { '<leader>pu', ':Lazy update<cr>', desc = 'Update' },

      -- Quit
      { '<leader>q', group = ' Quit' },
      { '<leader>qa', ':qall<cr>', desc = 'Quit All' },
      { '<leader>qb', ':bw<cr>', desc = 'Close Buffer' },
      { '<leader>qd', ':lua require("snacks").bufdelete()<cr>', desc = 'Delete Buffer' },
      { '<leader>qq', ':q<cr>', desc = 'Quit' },
      { '<leader>qw', ':wq<cr>', desc = 'Write and Quit' },

      -- Split/Window
      { '<leader>s', group = ' Split' },
      { '<leader>s/', '<C-w>s', desc = 'Split Below' },
      { '<leader>s\\', '<C-w>v', desc = 'Split Right' },
      { '<leader>sh', '<C-w>h', desc = 'Move Left' },
      { '<leader>sj', '<C-w>j', desc = 'Move Down' },
      { '<leader>sk', '<C-w>k', desc = 'Move Up' },
      { '<leader>sl', '<C-w>l', desc = 'Move Right' },
      { '<leader>sq', '<C-w>c', desc = 'Close Split' },

      -- Terminal
      { '<leader>t', group = ' Terminal' },

      -- Writing
      { '<leader>w', group = ' Writing' },
      { '<leader>wc', ':set spell!<cr>', desc = 'Spellcheck' },
      { '<leader>ww', ':w<cr>', desc = 'Write' },
      { '<leader>wq', ':wq<cr>', desc = 'Write and Quit' },

      -- Yank
      { '<leader>y', group = ' Yank' },
      { '<leader>ya', ':%y+<cr>', desc = 'Copy Whole File' },
    })

    -- Visual mode mappings
    which_key.add({
      mode = 'v',
      { '<leader>c', group = ' Code' },
      { '<leader>cf', ':lua vim.lsp.buf.format({async = true})<cr>', desc = 'Format Selection' },
      { '<leader>cs', ':sort<cr>', desc = 'Sort Asc' },
      { '<leader>cS', ':sort!<cr>', desc = 'Sort Desc' },

      { '<leader>g', group = ' Git' },
      { '<leader>gs', ":'<,'>Gitsigns stage_hunk<cr>", desc = 'Stage Hunk' },
      { '<leader>gr', ":'<,'>Gitsigns reset_hunk<cr>", desc = 'Reset Hunk' },
    })

    -- Non-leader mappings
    which_key.add({
      mode = 'n',
      { '<S-h>', ':bprevious<cr>', desc = 'Previous Buffer' },
      { '<S-l>', ':bnext<cr>', desc = 'Next Buffer' },
      { 'K', ':lua vim.lsp.buf.hover()<cr>', desc = 'LSP Hover' },
      { 'U', ':redo<cr>', desc = 'Redo' },

      { '[', group = ' Previous' },
      { '[g', ':Gitsigns prev_hunk<cr>', desc = 'Git Hunk' },
      { '[d', ':lua vim.diagnostic.goto_prev()<cr>', desc = 'Diagnostic' },

      { ']', group = ' Next' },
      { ']g', ':Gitsigns next_hunk<cr>', desc = 'Git Hunk' },
      { ']d', ':lua vim.diagnostic.goto_next()<cr>', desc = 'Diagnostic' },

      { 'g', group = 'Goto' },
      { 'gd', ':lua vim.lsp.buf.definition()<cr>', desc = 'Goto Definition' },
      { 'gr', ':lua vim.lsp.buf.references()<cr>', desc = 'References' },
      { 'gi', ':lua vim.lsp.buf.implementation()<cr>', desc = 'Implementation' },
    })
  end,
}
