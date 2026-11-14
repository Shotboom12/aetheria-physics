# How the physics works

Both systems drive bones through the engine's per-bone procedural transform slot (bone flag `0x80`, `CM2Model::SetBoneProceduralTransformByIndex`), after the engine has animated the model. Nothing is stored in a model file. Steps run at a fixed 1/120 s so the feel does not depend on frame rate.

## Cloaks (`CapePhysics.h`)

- Bones: retail skeletons carry a cape chain, key bones 36..40 (Cape1..Cape5), each the child of the previous, Cape1 hanging from the chest. The cloak geosets 1502..1510 are skinned to it. The code finds the bones by key id (scanning, so custom models that add the chain themselves, like the Sylvari female, work too) and only runs when all five are there and form a plain chain.
- Springs: each link gets a damped spring on its tip (the next link's pivot). The anchor is where the animated body would carry the tip; the lag is what swings. Links turn about their own pivots; the motion of the links above is subtracted so nothing is counted twice. Lag is weighted by depth^1.6 so the hem moves further than the shoulders and the cloak bends.
- World: starting, stopping, strafing, jumping and turning kick the springs; forward speed streams the cloak back (wind). Forward swing into the body is limited to 1.2 cm.
- Rest flare: a fixed backward posture for models whose chain is appended at the end of the bone list (custom models). Default 0.82 rad (owner-tuned for the Sylvari so the cloak clears the tail); retail models use `flare` = 0.
- Scope: the local player and other players within 45 yards; released (rigid) beyond that or when switched off.

Console names for `CapeSet(name, value)`: `enabled`, `zeta`, `gain`, `heightPower`, `maxBack`, `maxForward`, `maxSide`, `windMix`, `windMax`, `worldMix`, `turnMix`, `flare`, `customFlare`, `hz1`..`hz5`. Defaults: gain 2.0, maxBack 0.30, windMix 0.045, windMax 0.22, heightPower 1.6, zeta 0.42, hz 3.2/2.8/2.4/2.1/1.9.

## Jiggle (`JigglePhysics.h`)

- Breast bones of the retail female skeletons, indices (23, 26) or (28, 32), childless mirrored siblings; plus the pelvis for the rear (a mesh slider value, not a bone). Same spring model, plus a turn swing.
- The real motion is a rotation about the bone pivot (Rwise's capsule hung from the chest on a ball joint); `breastRotate` = 1 reproduces that (owner preference), 0 is a plain slide.
- Gotcha: the engine's bone matrices end in `worldTransform * view`, i.e. camera space. Anything reading them must multiply by the inverse of that matrix (`CM2Model::GetBoneAnimatedMatrix` does) or camera movement leaks into the springs.
- Off by default; the rear needs the local player's mesh rebuild, so the rear spring is local-player only.
- Console names for `JiggleSet(name, value)`: `enabled`, `breastHz`, `breastZeta`, `breastGain`, `breastMax`, `breastSide`, `breastRotate`, `breastDetune`, `breastUp`, `worldMix`, `turnMix`, `buttHz`, `buttZeta`, `buttGain`, `buttMax`.

## Applying to another tree

`patches/client-cape-physics.patch` is a unified diff (paths `a/<rel>` `b/<rel>` from the client root) against the aetheria-client source as it stood on 2026-11-13, jiggle hooks included; it adds `CapePhysics.h` hooks in `BodyShape.h`, `Unit_C.cpp`, `AetheriaGraphicsOptions.cpp` and `BodyShapeScripts.h`. Copy `CapePhysics.h` and `JigglePhysics.h` into `Engine/Source/Retail/`.
