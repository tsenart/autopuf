import Autopuf.Games

namespace Autopuf

inductive ProofStatus where
  | empiricalOnly
  | specified
  | partiallyProved
  | proved
  | counterexampleFound
  deriving Repr, DecidableEq

structure FormalClaim where
  id : String
  candidateFamily : String
  securityGame : SecurityGame
  assumptions : List String
  statement : String
  proofStatus : ProofStatus
  deriving Repr, DecidableEq

end Autopuf
