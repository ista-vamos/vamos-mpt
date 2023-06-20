# vamos-mpt

The implementation of the compiler for multi-trace prefix transducers (MPT).

MPTs are described with a simple format that we show with an example

```haskell
-- Declare events InputL, OutputL, and Write, all of them
-- with two parameters: `addr` which is 64-bit unsigned integer
-- and `x` which is 32-bit signed integer.
Event InputL, OutputL, Write {
  addr : UInt64,
  x    : Int32
}

-- The MPT called `OD` (the name is not relevant)
mpt OD {
  -- define two input traces, `t1` and `t2` whose type is
  -- "trace of InputL, OutputL, WriteL events"
  in t1 : [InputL, OutputL, Write], t2: [InputL, OutputL, Write];

  -- define a single output trace which is not in fact a trace,
  -- but a single boolean value. So this MPT reads two input traces
  -- and gives a single verdict which is either `true` or `false`.
  out o : Bool;

  -- the initial state of the MPT
  init q0;

  -- Define a self-loop transition over state q0, the transition
  -- matches the prefix expression `_*e1@{InputL + OutputL}` on both
  -- traces and if the matched input or output event is the same on
  -- both traces, the output of this is nothing, so the transducer
  -- continues reading traces.
  q0 -> q0 {
    t1: _*e1@{InputL + OutputL};
    t2: _*e2@{InputL + OutputL};
    cond: t1[e1] == t2[e2];
  }

  -- This transition from state q0 to q1 is triggered if the matched output
  -- events or end of stream events ($) are different and in that case
  -- `false` is put to output and transducer stops.
  q0 -> q1 {
    t1: _*e1@{OutputL + $};
    t2: _*e2@{OutputL + $};
    cond: t1[e1] != t2[e2];
    out: false;
  }

  -- When this transition is taken, the transducer also stops,
  -- but yields the value `true`.
  q0 -> q2 {
    t1: _*e1@{InputL + $};
    t2: _*e2@{InputL + $};
    cond: t1[e1] != t2[e2];
    out: true;
  }
}
```

## Prefix expressions

A prefix expression (PE) is similar to regular expression, but it matches only
a prefix of a string (trace in our case) and the shortest one at that.
PEs are formed with these rules:
 - every event name is a PE (e.g., `InputL` in the example above)
 - if `A` and `B` are PEs, then
   * `{A + B}` are PEs meaning `A` or `B`
   * `{A . B}` are PEs meaning `A` and then `B`
   * `{A . B}` or `{A B}` are PEs meaning `A` and then `B`
   * `{A}` is a PE (explicit parenthesis to alter priorities)
 - if `A` is a PE and `B` is a PE matching _exactly one_ event, i.e., `B` is either
   an event name or a disjunction (+) of event names, then `{A*B}` is a PE
   meaning `A` until the first occurence of `B`. More precisely, `A*B` is defined
   as `B + AB + AAB + AAAB ...` evaluated from left to right.

We use `{` and `}` to group expressions together, to avoid too many `(` and `)`
when we allow matched events to have parameters (future work).
We can avoid `{` and `}` if we keep in mind that the highest priority has `.` then
`*` and then `+`. So we can write the expression `{{{A.A}+B}*C}` as `{A.A + B}*C`.

## Multi-trace PEs

TBD
