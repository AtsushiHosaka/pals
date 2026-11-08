<!-- 2026-11-08 調査。宣言名は Mathlib（v4.35.0 固定の rev 56a00585）と Stacks（rev 5ed82d14）のソースを grep して確認した。主要な数件（PrimeSpectrum.irreducibleSpace_iff_isPrime_nilradical、isIdempotentElemEquivClopens、IdealSheafData、IsQuasicoherent、topologicalKrullDim、IsProper、および Mathlib に IsAmple と picardGroup が無いこと）は別途 grep で再確認した。全行を再確認したわけではない。 -->

# 代数幾何の「文を書ける範囲」目録 (Mathlib / StacksCore / StacksFrontier)

調査方法: 以下の3つのソースを読んで grep した。ビルド、型クラス解決、モデル呼び出しは行っていない。
- Mathlib (Lean v4.35.0 固定): `<workspace>/.lake/packages/mathlib/Mathlib/`
- Stacks repo: `<workspace>/.lake/packages/Stacks/` (StacksCore 445 ファイル、StacksFrontier 62,527 ファイル、うち `StacksFrontier/AlgebraicGeometry/` は 43,974 ファイル)

「文を書ける」の意味: 命題の文に現れる定数が、その列の範囲内の宣言だけでできる。証明が通るか、型クラス解決が通るかは問わない。型クラス解決は build で確かめていないので、「Mathlib のみ」は「宣言が存在する」という意味。

## 結論

- **StacksCore は代数幾何を持たない。Mathlib は持つ。** StacksCore を `grep -rli scheme` しても 0 件。一方 Mathlib は Scheme、Spec、Proj、射の性質のほぼ全て、`IsProper`、付価判定法 (valuative criterion)、Zariski の主定理、`Scheme.Modules`、`IsQuasicoherent`、`IdealSheafData`、`topologicalKrullDim` を持つ。
- **Mathlib だけで文を書ける:** スキームとその射の標準的な性質 (affine / 準コンパクト / 分離 / 局所有限型 / 有限 / 平坦 / 滑らか / étale / 固有 / 閉・開はめ込み)、Spec/Proj、茎・剰余体・関数体、reduced / integral / noetherian、ファイバー積と基底変換、イデアル層、擬連接層・局所自由層、`Sheaf.H` による層コホモロジー、位相的クルル次元、`PrimeSpectrum` 側の可換環論の橋渡し。
- **Frontier が必要:** Mathlib に定義がない概念。具体的には、豊富 (ample) な可逆層 `IsAmple`、Picard 群 `Scheme.picardGroup`、射影的射 `IsProjective` と射影束 `schemeProjectiveBundle`、可逆層の `Stacks.SheafOfModules.IsInvertible`、実効 Cartier 因子 `IsEffectiveCartierDivisor`、代数的空間・代数的スタック、双対性 (Duality) の周辺。
- **Frontier の定義でも、中身が Mathlib 定数だけのものがある。** `IsVariety`、`IsCurve` はその例で、Mathlib 定数を並べて直接書ける。ただし PALS が Frontier の名前を許すか、展開形で書かせるかは別の判断になる。
- **注意:** `ℙⁿ` を名前で持つ宣言は Mathlib にない。ただし `Proj (MvPolynomial.homogeneousSubmodule (Fin (n+1)) R)` と書ける (`MvPolynomial.gradedAlgebra` の instance は存在する)。Mathlib に `Pic`、ample、`Cartier 因子`、`Scheme 上のコホモロジー専用の記法` は存在しない。
- **要 build 確認:** `Sheaf.H` を `Scheme.Modules` に適用する書き方 (目録の「層コホモロジー」の行) は型クラス解決 (`HasExt` など) がビルドで通るか未検証。Frontier の `SchemeIsoStructureSheafCohomology.lean` が同じ書き方をしているので、通る見込みは高い。

## 目録

略記: M = Mathlib の `Mathlib/` 配下、F = `Stacks/StacksFrontier/` 配下。名前空間は `AlgebraicGeometry` で、省略している。

| 分野 | 概念 | 文を書ける? | 主な宣言名 (grep 確認済み) | 場所 | 備考 |
|---|---|---|---|---|---|
| スキーム | Scheme と射 | Mathlib のみ | `Scheme`, `Scheme.Hom`, `Scheme.Opens`, `Scheme.Hom.stalkMap`, `Scheme.Hom.appLE` | M `AlgebraicGeometry/Scheme.lean` | 射は圏論の `X ⟶ Y`。宇宙は `Scheme.{u}` |
| スキーム | Spec と Γ | Mathlib のみ | `Spec (R : CommRingCat)`, `Spec.map`, `Scheme.Γ`, `Scheme.ΓSpecIso`, `Spec.stalkIso` | M `Scheme.lean` (466, 475, 572, 602), `AffineScheme.lean` (1289) | 環は `CommRingCat`。`Spec (.of R)` と書く |
| スキーム | アフィン性 | Mathlib のみ | `IsAffine`, `IsAffineOpen`, `Scheme.affineOpens`, `Scheme.isBasis_affineOpens`, `Scheme.Hom.toSpecΓ` | M `AffineScheme.lean` (57, 249, 253, 303) | 準アフィン `Scheme.IsQuasiAffine` は `QuasiAffine.lean` (`@[stacks 01P6]`) |
| スキーム | 射の局所性・被覆 | Mathlib のみ | `IsZariskiLocalAtTarget`, `Scheme.OpenCover`, `IsOpenImmersion` | M `Morphisms/Basic.lean`, `Cover/Open.lean` (40), `OpenImmersion.lean` (36) | `IsOpenImmersion` は `MorphismProperty` の abbrev |
| 射の性質 | 準コンパクト・準分離 | Mathlib のみ | `QuasiCompact`, `QuasiSeparated`, `CompactSpace X` | M `Morphisms/QuasiCompact.lean` (41), `QuasiSeparated.lean` (48) | スキームが準コンパクトなことは `CompactSpace X` |
| 射の性質 | 分離 (射・スキーム) | Mathlib のみ | `IsSeparated` (射、対角が閉はめ込み), `Scheme.IsSeparated` (スキーム) | M `Morphisms/Separated.lean` (44, 332) | 射は `IsSeparated f`、スキームは `Scheme.IsSeparated X` で区別 |
| 射の性質 | 局所有限型・局所有限表示 | Mathlib のみ | `LocallyOfFiniteType`, `LocallyOfFinitePresentation` | M `Morphisms/FiniteType.lean` (42), `FinitePresentation.lean` (46) | |
| 射の性質 | 有限・整・アフィン射 | Mathlib のみ | `IsFinite`, `IsIntegralHom`, `IsAffineHom` | M `Morphisms/Finite.lean` (41), `Integral.lean` (35), `Affine.lean` (48) | `IsFinite.iff_isProper_and_locallyQuasiFinite` が Mathlib にある (`ZariskisMainTheorem.lean`, `@[stacks 02LS]`) |
| 射の性質 | 固有 (proper) | Mathlib のみ | `IsProper` (= `IsSeparated` ∧ `UniversallyClosed` ∧ `LocallyOfFiniteType`), `UniversallyClosed` | M `Morphisms/Proper.lean` (41), `UniversallyClosed.lean` (43) | 固有は Mathlib にある。`Surjective` は `Morphisms/UnderlyingMap.lean` (58) |
| 射の性質 | 平坦 | Mathlib のみ | `Flat` | M `Morphisms/Flat.lean` (42) | 忠実平坦降下は `FlatDescent.lean`、`FlatMono.lean` |
| 射の性質 | 滑らか・étale・非分岐 | Mathlib のみ | `Smooth`, `SmoothOfRelativeDimension`, `Etale`, `FormallyUnramified`, `WeaklyEtale.lean` | M `Morphisms/Smooth.lean` (59, 127), `Etale.lean` (39), `FormallyUnramified.lean` (54) | 定義はアフィン開集合上の環準同型の性質を使う |
| 射の性質 | 開・閉・局所閉はめ込み | Mathlib のみ | `IsOpenImmersion`, `IsClosedImmersion`, `IsImmersion`, `IsPreimmersion` | M `Morphisms/ClosedImmersion.lean` (44), `Immersion.lean` (45), `Preimmersion.lean` (33) | |
| 射の性質 | 準有限・普遍開・普遍単射 | Mathlib のみ | `LocallyQuasiFinite`, `Scheme.Hom.QuasiFiniteAt`, `UniversallyOpen`, `UniversallyInjective` | M `Morphisms/QuasiFinite.lean` (72, 333), `UniversallyOpen.lean` (40), `UniversallyInjective.lean` (46) | |
| 射の性質 | 付価判定法 | Mathlib のみ | `ValuativeCriterion`, `ValuativeCriterion.Existence`, `UniversallyClosed.of_valuativeCriterion`, `IsProper.of_valuativeCriterion` | M `ValuativeCriterion.lean` (54, 79, 238, 342) | 固有の同値は `IsProper.eq_valuativeCriterion` (331) |
| 射の性質 | Zariski の主定理 | Mathlib のみ | `Scheme.Hom.exists_isIso_morphismRestrict_toNormalization` (`@[stacks 03GW]`), `IsFinite.iff_isProper_and_locallyQuasiFinite` | M `ZariskisMainTheorem.lean` (205, 381) | Stacks 02LN より弱い形 (ファイル内コメント)。`exists_etale_isCompl_of_quasiFiniteAt` もある |
| Spec/Proj | Proj と射影スペクトラム | Mathlib のみ | `ProjectiveSpectrum`, `Proj` (`«Proj»`), `Proj.toSpecZero`, `Proj.structureSheaf`, `ProjectiveSpectrum.basicOpen`, `Proj.projIsoSpec` | M `ProjectiveSpectrum/Topology.lean` (53, 331), `Scheme.lean` (849, 862), `StructureSheaf.lean` (207) | `Proj` は ℕ 次数環 `𝒜 : ℕ → σ` から作る。`Proj 𝒜` の基本開集合 `D₊(f) ≅ Spec A⁰_f` は `projIsoSpec` |
| Spec/Proj | Proj の固有性 | Mathlib のみ | `Proj.toSpecZero`, 固有性の instance (`IsProper (Proj.toSpecZero 𝒜)`) | M `ProjectiveSpectrum/Proper.lean` (83, 131, 372) | `[Algebra.FiniteType (𝒜 0) A]` が条件 |
| Spec/Proj | 射影空間 ℙⁿ | Mathlib のみ (名前なし、`Proj` で書く) | `Proj (MvPolynomial.homogeneousSubmodule (Fin (n+1)) R)`, `MvPolynomial.gradedAlgebra` | M `RingTheory/MvPolynomial/Homogeneous.lean` (613) | Mathlib に `ℙⁿ` 専用の名前はない (`ProjectiveSpace` を grep して 0 件)。Frontier には `projectiveSpaceOverRing` がある (F `AlgebraicGeometry/Constructions/ProjectiveSpace.lean:181`) が、中身は Mathlib の `Proj` ではなく `pullback ... projectiveSpaceAtUniverse` なので同じ文にならない可能性あり (未確認) |
| Spec/Proj | アフィン空間 𝔸ⁿ | Mathlib のみ | `AffineSpace n S` (記法 `𝔸(n; S)`), `AffineSpace.toSpecMvPoly`, `AffineSpace.coord` | M `AlgebraicGeometry/AffineSpace.lean` (43, 69, 98) | 添字型 `n : Type u` を取る |
| 構造層 | 構造層・茎・剰余体 | Mathlib のみ | `X.presheaf.stalk x`, `Scheme.residueField`, `Scheme.fromSpecResidueField`, `Scheme.Hom.residueFieldMap`, `Scheme.fromSpecStalk` | M `ResidueField.lean` (45, 237, 123), `Stalk.lean` (63) | 構造層は `X.presheaf` / `X.sheaf`。局所環は `IsLocalRing (X.presheaf.stalk x)` |
| 構造層 | Spec の構造層 | Mathlib のみ | `StructureSheaf` 周辺、`Spec.locallyRingedSpaceObj`, `Spec.sheafedSpaceObj` | M `StructureSheaf.lean`, `Spec.lean` (86, 183) | |
| 性質 | reduced / integral | Mathlib のみ | `IsReduced`, `IsIntegral`, `isIntegral_iff_irreducibleSpace_and_isReduced` | M `Properties.lean` (68, 239, 306) | integral ⇒ `IsDomain Γ(X, ⊤)` |
| 性質 | noetherian・artinian | Mathlib のみ | `IsLocallyNoetherian`, `IsNoetherian`, `IsLocallyArtinian` | M `Noetherian.lean` (54, 277), `Artinian.lean` | |
| 性質 | 正規・正則スキーム | Mathlib のみ (茎ごとに書く) | `IsIntegrallyClosed (X.presheaf.stalk x)`, `IsRegularLocalRing (X.presheaf.stalk x)`, `IsRegularRing` | M `RingTheory/RegularLocalRing/Defs.lean` (52, 93) | 「正規スキーム」「正則スキーム」を名前で持つクラスは Mathlib にない (grep 0 件)。茎の条件として書く。Frontier の `IsNormal` は射の性質 (F `Morphisms/CohenMacaulay/NormalMorphism.lean:54`) |
| 性質 | Cohen-Macaulay | Frontier が必要 | `AlgebraicGeometry.IsCohenMacaulay` (射), `IsCohenMacaulayAt` | F `AlgebraicGeometry/Morphisms/CohenMacaulay/Defs.lean` (73, 82) | Mathlib にスキームの CM はない。環の側 (`IsCohenMacaulayLocalRing`) は Mathlib の `RingTheory` にあるか未確認 |
| 性質 | 関数体 | Mathlib のみ | `Scheme.functionField`, `Scheme.Hom.fiber` | M `FunctionField.lean` (37), `Fiber.lean` (37) | `[IrreducibleSpace X]` を仮定して使う |
| 構成 | 貼り合わせ | Mathlib のみ | `Scheme.GlueData`, `Scheme.GlueData.glued`, `Scheme.GlueData.ι` | M `Gluing.lean` (91, 159, 163) | 一般化は `GluingOneHypercover.lean`、`RelativeGluing.lean` |
| 構成 | ファイバー積・基底変換 | Mathlib のみ | `pullback f g`, `pullback.fst`, `pullback.snd`, `pullback.diagonal`, `Scheme.Hom.fiber`, `instance : HasPullbacks Scheme` | M `Pullbacks.lean` (482), `Fiber.lean` | ファイバー積は圏論の `CategoryTheory.Limits.pullback` |
| 構成 | 有理写像・双有理 | Mathlib のみ | `Scheme.PartialMap`, `Scheme.RationalMap`, `Scheme.Birational`, `BirationalOver` | M `Birational/RationalMap.lean` (374), `Birational/Birational.lean` (181, 203) | |
| 構成 | 正規化 | Mathlib のみ | `Scheme.Hom.toNormalization`, `Scheme.Hom.fromNormalization`, `Scheme.Hom.normalization` | M `Normalization.lean` | |
| 構成 | 閉点・点 (幾何学的点) | Mathlib のみ | `Scheme.fromSpecResidueField`, `SpecToEquivOfField`, `Spec.residueFieldIso` | M `ResidueField.lean` (237, 301, 409) | 体値点は `Spec K ⟶ X`。幾何的に reduced / irreducible / integral / connected は `Geometrically/*.lean` (`GeometricallyReduced` など) |
| イデアル層 | IdealSheaf | Mathlib のみ | `Scheme.IdealSheafData`, `IdealSheafData.support`, `IdealSheafData.subschemeι`, `Scheme.nilradical`, `Scheme.Hom.ker` | M `IdealSheaf/Basic.lean` (64, 327, 528, 691), `IdealSheaf/Subscheme.lean` | 閉部分スキームとイデアル層の対応。Frontier の `IsEffectiveCartierDivisor` はこのクラスを引数に取る |
| 層上の加群 | `Scheme.Modules` | Mathlib のみ | `Scheme.Modules` (= `SheafOfModules X.ringCatSheaf`), `Scheme.Modules.pullback`, `Scheme.Modules.pushforward`, `Scheme.Modules.restrict` | M `AlgebraicGeometry/Modules/Sheaf.lean` (36, 166, 183, 346) | 随伴 `pullbackPushforwardAdjunction` もある |
| 層上の加群 | 擬連接・局所自由・有限型・有限表示 | Mathlib のみ | `SheafOfModules.IsQuasicoherent`, `SheafOfModules.IsFiniteType`, `SheafOfModules.IsFinitePresentation`, `SheafOfModules.IsLocallyFree` (`@[stacks 01C6]`) | M `Algebra/Category/ModuleCat/Sheaf/Quasicoherent.lean` (254, 270), `Generators.lean` (142), `LocallyFree.lean` (61) | クラス名は `IsQuasicoherent` (小文字の c)。`Scheme.Modules` 上で `(tilde M).IsQuasicoherent` として実際に使用 (`Modules/Tilde.lean` 457)。**「連接」(coherent) を名前で持つクラスは見つからなかった**。有限型 ∧ 擬連接の組み合わせか、有限表示で書く |
| 層上の加群 | `M~` (tilde) | Mathlib のみ | `tilde`, `tilde.functor`, `tilde.adjunction`, `Scheme.Modules.fromTildeΓ` | M `AlgebraicGeometry/Modules/Tilde.lean` (153, 342, 256) | アフィン上の擬連接 ≃ 加群の完全な同値は、`fromTildeΓ` が擬連接で同型 (843) まで。圏同値の形の文は未確認 |
| 層上の加群 | 可逆層・線束 | Frontier が必要 | `Stacks.SheafOfModules.IsInvertible`, `AlgebraicGeometry.SheafOfModules.IsInvertible` | F `Algebra/Category/ModuleCat/Sheaf/TensorInvertible.lean:130`, `Topology/Sheaves/Modules/Invertible.lean:85` | Mathlib に `IsInvertible` なし (grep 0 件)。「局所的に `𝒪` と同型」は Mathlib の `IsLocallyFree` + 階数 1 では書けない (階数の定義は未確認) |
| コホモロジー | 層コホモロジー `Hⁿ(X, F)` | Mathlib のみ (要 build 確認) | `CategoryTheory.Sheaf.H`, `Sheaf.H'`, `Sheaf.H.map`, `SheafOfModules.toSheaf` | M `CategoryTheory/Sites/SheafCohomology/Basic.lean` (57, 85, 112), `Algebra/Category/ModuleCat/Sheaf.lean` (88) | `Sheaf.H ((SheafOfModules.toSheaf X.ringCatSheaf).obj M) n` の形を Frontier が使用 (F `AlgebraicGeometry/SchemeIsoStructureSheafCohomology.lean:40`)。この文の定数は全て Mathlib。`HasDerivedCategory.standard` を local instance にしている |
| コホモロジー | Čech コホモロジー | Mathlib のみ | `Sheaf.cechComplexFunctor`, `cosimplicialObjectFunctor`, `cochainComplexFunctor`, Mayer-Vietoris `δ` | M `CategoryTheory/Sites/SheafCohomology/Cech.lean` (43, 53, 65), `MayerVietoris.lean` | スキーム専用のスキーム上 Čech は Mathlib にない。比較定理 (Čech と導来の一致) は未確認 |
| コホモロジー | スキーム専用の導来関手・ `Rf_*` ・ `H^i` 記法 | Frontier が必要 | `Scheme.Modules.pushforward` の `rightDerivedPlus`, `cohomologyIsoSectionsRightDerivedPushforward`, `sectionsFunctor` | F `AlgebraicGeometry/Cohomology/AffineBase.lean` (128, 149), `AffineBaseNatCast.lean` (60) | 文は `rightDerivedPlus` (Mathlib) と `quasicoherentInclusion` (F `Cohomology/AffineBase.lean:71`) など Frontier 定義を混ぜる。`Stacks.DerivedIndexing.rightDerivedIso` も Frontier |
| コホモロジー | アフィン上の消滅 | Frontier が必要 (証明側) / 文は Mathlib で書ける | Frontier 側: `AffineCohomologyVanishing/*`, 例 `Cohomology/AffineBase.lean` | F `AlgebraicGeometry/AffineCohomologyVanishing/Basic.lean` ほか | `Hⁿ(Spec A, M~) = 0 (n>0)` の文は、`Sheaf.H` と `tilde` (どちらも Mathlib) で書ける。Frontier が必要なのは証明を再利用したい場合 |
| コホモロジー | étale / ℓ進コホモロジー | Mathlib のみ (サイトと `Sheaf.H` で) | `Scheme.smallEtaleTopology`, `etaleTopology`, `Scheme.EllAdicCohomology`, `Scheme.ellAdicSheaf` | M `AlgebraicGeometry/Sites/Etale.lean` (40, 50), `Sites/ElladicCohomology.lean` | 主要な性質 (比較、基底変換) は Frontier の `EtaleCohomology/*` (例 `smallEtaleCohomologyPresheaf`, F `EtaleCohomology/TorsionHigherDirectImage.lean:260`) |
| サイト | Zariski / fppf / fpqc / pro-étale | Mathlib のみ | `zariskiTopology`, `fppfTopology`, `fpqcTopology`, `Scheme.ProEt` 周辺 | M `Sites/BigZariski.lean` (51), `Fpqc.lean` (54, 76), `Proetale.lean` | |
| 因子 | Weil 因子・代数的サイクル | Mathlib のみ | `AlgebraicCycle X R`, `IsWeilDivisor`, `weilDivisors` | M `AlgebraicGeometry/AlgebraicCycle/Basic.lean` (44, 143, 164) | 余次元 1 の台のサイクルとして定義 |
| 因子 | 実効 Cartier 因子 | Frontier が必要 | `IsLocallyPrincipal`, `IsEffectiveCartierDivisor`, `EffectiveCartierDivisor` | F `AlgebraicGeometry/Divisors/EffectiveCartier.lean` (73, 79), `Divisors/RegularSectionCorrespondence.lean` (280) | 文は `X.IdealSheafData` (Mathlib) と `SheafOfModules.IsInvertible` (Frontier) を使うので Frontier が強制される |
| 因子 | Picard 群 | Frontier が必要 | `Scheme.picardGroup`, `pullbackPicardHom`, `picardGroupAddEquivOfIso` | F `AlgebraicGeometry/PicardGroup/Scheme.lean:71`, `PullbackHom.lean` (62, 113) | `Stacks.SheafOfModules.PicardGroup` に依存 (`@[stacks 01CX]`)。Mathlib に `Pic` なし (grep 0 件) |
| 因子 | 豊富 (ample) な可逆層 | Frontier が必要 | `Scheme.Modules.IsAmple` (`@[stacks 01PS]`) | F `AlgebraicGeometry/Ample/Defs.lean:95` | 定義は `Stacks.SheafOfModules.Invertible.tensorPower`, `nonvanishingOpen` を使う。Mathlib に ample なし (grep 0 件) |
| 因子 | 射影的射・射影束 | Frontier が必要 | `IsProjective` (射), `IsQuasiProjective`, `schemeProjectiveBundle` | F `AlgebraicGeometry/Morphisms/Projective/Basic.lean:170`, `QuasiProjective/Basic.lean:77`, `SheafSymmetricAlgebra/Scheme.lean:176` | `IsProjective` の定義が `schemeProjectiveBundle` (Frontier) を使う。ただし「X が固有でかつ豊富な層がある」などの言い換えも Frontier の `IsAmple` が必要 |
| 次元論 | 位相的クルル次元 | Mathlib のみ | `topologicalKrullDim`, `ringKrullDim`, `PrimeSpectrum.topologicalKrullDim_eq_ringKrullDim` | M `Topology/KrullDimension.lean` (37), `RingTheory/KrullDimension/Basic.lean` (26) | スキームの次元は `topologicalKrullDim X`。`ringKrullDim_stalk_eq_coheight` が M `Properties.lean` (375) にある |
| 次元論 | 曲線・多様体 | Mathlib 定数だけに展開できる | `IsVariety` (= `IsIntegral X` ∧ `IsSeparated f` ∧ `LocallyOfFiniteType f` ∧ `QuasiCompact f`), `IsCurve` (+ `topologicalKrullDim X = 1`), `IsProperVariety` | F `AlgebraicGeometry/Variety/Defs/Basic.lean:50, 57`, `Variety/Curve/Defs.lean:46` | クラス名は Frontier だが定義は全て Mathlib 定数。展開形で書けば Mathlib のみ。`@[stacks 020D]`, `@[stacks 0A23]` |
| 次元論 | Riemann-Roch・双対性・Euler 標数 | Frontier が必要 | `asymptotic_riemann_roch` (`@[stacks 0BJ8]`), `degreeWithRespectTo`, `globalSectionsOverField`, `tensorPower` | F `AlgebraicGeometry/Variety/NumericalIntersections/AsymptoticRiemannRoch.lean:466`, `EulerCharAdditivity/Basic.lean` | 文が `IsAmple`、`degreeWithRespectTo` (Frontier 定義) を使う |
| 空間・スタック | 代数的空間・代数的スタック | Frontier が必要 | `BigFppfSite`, `AlgebraicStacks`, `Spaces/*`, `Stacks/*` | F `AlgebraicGeometry/Topologies/Fppf.lean:110`, `Stacks/AlgebraicStackSmallModel.lean:146` | Mathlib になし |
| 空間・スタック | ブローアップ | Frontier が必要 | `blowUp` | F `AlgebraicGeometry/Blowup/ReesAlgebra/BlowUp.lean:63`, `Blowup/ReesSheafData.lean:233` | 文は `X.IdealSheafData` (Mathlib) を取るが、`blowUp` 自体が Frontier |
| 空間・スタック | 微分形式の層・Kähler 微分の層 | Frontier が必要 (一部は Mathlib の前層で可) | `PresheafOfModules.HasDifferentials`, `relativeDifferentials'` (前層レベル), 層レベルは F `Topology/Sheaves/Modules/Differentials.lean` | M `Algebra/Category/ModuleCat/Differentials/Presheaf.lean` (122, 188), F `Topology/Sheaves/Modules/Differentials.lean` | 環レベルの `KaehlerDifferential` は Mathlib。スキーム上の Ω_{X/S} を名前で持つ宣言は未確認 |
| 群スキーム | アフィン群スキーム・Hopf 代数 | Mathlib のみ | `hopfSpec`, `bialgSpec`, `algSpec`, `Spec.mapMulEquiv` | M `AlgebraicGeometry/Group/Affine.lean` (162, 177, 269), `Group/Abelian.lean`, `Group/Smooth.lean` | |
| 楕円曲線 | Weierstrass 曲線 | Mathlib のみ | `WeierstrassCurve`, `IsIntegral`, `HasGoodReduction` | M `AlgebraicGeometry/EllipticCurve/Weierstrass.lean`, `Reduction.lean` (58, 324) | スキームではなく係数で書く方式。`EllipticCurve/Projective`, `Jacobian` もある |
| 可換環論の橋渡し | PrimeSpectrum と Zariski 位相 | Mathlib のみ | `PrimeSpectrum`, `PrimeSpectrum.zariskiTopology`, `PrimeSpectrum.basicOpen`, `PrimeSpectrum.zeroLocus`, `PrimeSpectrum.vanishingIdeal` | M `RingTheory/Spectrum/Prime/Defs.lean` (34), `Topology.lean` (125, 504) | StacksCore の `RingTheory/Spectrum` ディレクトリがあるが中身は未確認 |
| 可換環論の橋渡し | 冪等元 ↔ 連結性 | Mathlib のみ | `PrimeSpectrum.isIdempotentElemEquivClopens` (`@[stacks 00EE]`), `PrimeSpectrum.primeSpectrumProd`, `primeSpectrumProdHomeo` | M `RingTheory/Spectrum/Prime/Topology.lean` (1400, 446) | 積の Spec は `AlgebraicGeometry/Limits.lean` の `coprodSpec` |
| 可換環論の橋渡し | 冪零根基 ↔ 既約性 | Mathlib のみ | `PrimeSpectrum.irreducibleSpace_iff_isPrime_nilradical`, `isIrreducible_zeroLocus_iff`, `discreteTopology_iff_finite_isMaximal_and_sInf_le_nilradical` | M `RingTheory/Spectrum/Prime/Topology.lean` (274, 252, 306) | スキーム側は `isIntegral_iff_irreducibleSpace_and_isReduced` |
| 可換環論の橋渡し | Jacobson 環・構成可能集合 | Mathlib のみ | `IsJacobsonRing`, `PrimeSpectrum.isJacobsonRing_iff_jacobsonSpace`, `isConstructible_range_comap` (Chevalley) | M `RingTheory/Jacobson/Ring.lean` (60), `Spectrum/Prime/Jacobson.lean` (61), `Prime/Chevalley.lean` (55) | |

## 調べきれなかった点

- **ビルドしていない。** 「Mathlib のみ」は宣言が存在することを意味し、型クラス解決 (`HasExt`、`HasSheafify` など) の成否は未検証。特に `Scheme.Modules` に `Sheaf.H` を適用する行は build 確認が必要。
- **「連接層 (coherent)」の Mathlib クラス**は見つからなかった。`IsQuasicoherent` と `IsFiniteType` (または `IsFinitePresentation`) の組み合わせで書けるかは未確認。
- **局所自由層の階数**を Mathlib で書く方法 (可逆層 = 階数 1 の局所自由層) は未確認。
- **Cohen-Macaulay (環側)** の Mathlib 宣言 (`IsCohenMacaulayLocalRing` の有無) は未確認。`RingTheory` 配下にあるかを grep していない。
- **`projectiveSpaceOverRing` (Frontier) と `Proj (homogeneousSubmodule ...)` (Mathlib) の同型の有無**は未確認。PALS が ℙⁿ を許す場合、どちらで書くかを決める必要がある。
- **StacksCore の `RingTheory/Spectrum`** の中身は見ていない。StacksCore が `PrimeSpectrum` に関する独自の定理を持つかは未確認。
- **Frontier 62,527 ファイルを網羅したわけではない。** 行ごとに代表的な宣言を1〜2件確認しただけで、各 Frontier ファイルの import 先まで再帰的に追跡してはいない。「文が Frontier 定数を使う」と書いた行は、該当ファイルの定義本文で確認したものに限る (`IsAmple`、`IsProjective`、`IsEffectiveCartierDivisor`、`picardGroup`、`asymptotic_riemann_roch`)。
- Frontier は AI 生成で未レビューである。Frontier の宣言を文に使う場合、その定義が Stacks の記述と一致する保証はない。
