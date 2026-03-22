import Lake
open Lake DSL

package «autopuf» where

@[default_target]
lean_lib Autopuf where

lean_exe «autopuf-formal» where
  root := `Main

