# Liquidity Map

## ADLC Binding
Phase: Architecture Design, Testing & Evaluation.

## Purpose
Stores strong liquidity locations and level-quality notes.

## Required Fields
- Timestamp
- Symbol
- Primary liquidity levels
- Level strength
- Current price relation
- Invalidated levels
- Liquidity Agent decision

## Control Rule
Mid-range price action or weak location returns `NO_TRADE`.

