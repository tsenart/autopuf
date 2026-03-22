import Autopuf

open Autopuf

def usage : IO UInt32 := do
  IO.eprintln "usage: autopuf-formal differential classical_crp <challenge_count> <response_width> <replay_window>"
  pure 1

def printReference (reference : ClassicalCrpReference) : IO UInt32 := do
  IO.println s!"supported={reference.supported}"
  IO.println s!"family=classical_crp"
  IO.println s!"challenge_count={reference.challengeCount}"
  IO.println s!"response_width={reference.responseWidth}"
  IO.println s!"replay_window={reference.replayWindow}"
  IO.println s!"expected_lifetime={reference.expectedLifetime}"
  IO.println s!"security_game={reference.securityGame}"
  pure 0

def parseNat? (value : String) : Option Nat :=
  value.toNat?

def runDifferential : List String -> IO UInt32
  | ["classical_crp", challengeCount, responseWidth, replayWindow] =>
      match parseNat? challengeCount, parseNat? responseWidth, parseNat? replayWindow with
      | some challengeCountNat, some responseWidthNat, some replayWindowNat =>
          printReference (classicalCrpReference challengeCountNat responseWidthNat replayWindowNat)
      | _, _, _ => do
          IO.eprintln "all differential arguments must be natural numbers"
          pure 1
  | _ => usage

def main : List String -> IO UInt32
  | "differential" :: rest => runDifferential rest
  | _ => usage
