namespace Autopuf

abbrev ParamMap := List (String × String)

structure Candidate where
  id : String
  family : String
  params : ParamMap
  deriving Repr, DecidableEq

structure Challenge where
  label : String
  deriving Repr, DecidableEq

structure Response where
  label : String
  deriving Repr, DecidableEq

structure Verifier where
  model : String
  deriving Repr, DecidableEq

structure Adversary where
  name : String
  deriving Repr, DecidableEq

end Autopuf
