require('core.options')
require('core.functions')
require('core.keys')
require('core.autocmd')
require('core.lazy')
-- Add user configs to this module
pcall(require, 'user')
