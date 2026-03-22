import Autopuf.Claims

namespace Autopuf

structure ClassicalCrpReference where
  supported : Bool
  challengeCount : Nat
  responseWidth : Nat
  replayWindow : Nat
  expectedLifetime : Nat
  securityGame : String
  deriving Repr, DecidableEq

structure BridgeCheck where
  supported : Bool
  differentialCheckId : Option String
  deriving Repr, DecidableEq

structure ClaimBinding where
  claim : FormalClaim
  relatedRuns : List String
  bridgeCheck : BridgeCheck
  deriving Repr, DecidableEq

def classicalCrpExpectedLifetime (challengeCount replayWindow : Nat) : Nat :=
  if replayWindow == 0 then
    0
  else
    max 1 (challengeCount / replayWindow)

def classicalCrpReference
    (challengeCount responseWidth replayWindow : Nat) : ClassicalCrpReference :=
  {
    supported := challengeCount > 0 && responseWidth > 0 && replayWindow > 0
    challengeCount := challengeCount
    responseWidth := responseWidth
    replayWindow := replayWindow
    expectedLifetime := classicalCrpExpectedLifetime challengeCount replayWindow
    securityGame := "bounded_crp_authentication"
  }

end Autopuf
