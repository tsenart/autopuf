import Autopuf.Model

namespace Autopuf

structure SecurityGame where
  name : String
  assumptions : List String
  deriving Repr, DecidableEq

structure GameInstance where
  candidate : Candidate
  verifier : Verifier
  adversary : Adversary
  game : SecurityGame
  deriving Repr, DecidableEq

end Autopuf
