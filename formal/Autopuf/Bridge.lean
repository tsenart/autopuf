import Autopuf.Claims

namespace Autopuf

structure BridgeCheck where
  supported : Bool
  differentialCheckId : Option String
  deriving Repr, DecidableEq

structure ClaimBinding where
  claim : FormalClaim
  relatedRuns : List String
  bridgeCheck : BridgeCheck
  deriving Repr, DecidableEq

end Autopuf
