"""Original, general school arithmetic cards in the existing number-theory profile.

Sources identify concepts; the statements and sketches are first-party authoring.
Every witness still needs the production preparation script's real Lean compile.
"""

from __future__ import annotations

from html import escape

TYPED = "urn:pals:openmath:typed-number-theory:v1"
STANDARD = "http://www.openmath.org/cd"


def symbol(cd: str, name: str, *, standard: bool = False) -> str:
    return f'<OMS cdbase="{STANDARD if standard else TYPED}" cd="{cd}" name="{name}"/>'


def variable(name: str) -> str:
    return f'<OMV name="{escape(name, quote=True)}"/>'


def nt(name: str, *args: str) -> str:
    return "<OMA>" + symbol("numbertheory1", name) + "".join(args) + "</OMA>"


def literal(n: int, sort: str = "Nat") -> str:
    return nt("nat_literal" if sort == "Nat" else "int_literal", f"<OMI>{n}</OMI>")


def relation(name: str, *args: str) -> str:
    cd = "logic1" if name in {"and", "or", "implies"} else "relation1"
    return "<OMA>" + symbol(cd, name, standard=True) + "".join(args) + "</OMA>"


def cards() -> list[dict]:
    result = []
    a, b, c = map(variable, "abc")

    def add(key, names, sort, statement, body, lean, proof, reason):
        declarations = "".join(
            "<OMATTR><OMATP>" + symbol("typed1", "type")
            + symbol("numbertheory1", sort) + "</OMATP>" + variable(n) + "</OMATTR>"
            for n in names.split()
        )
        xml = '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0"><OMBIND>'
        xml += symbol("typed1", "forall") + "<OMBVAR>" + declarations + "</OMBVAR>"
        xml += body + "</OMBIND></OMOBJ>"
        result.append(dict(
            id="school26_" + key, profile_id="typed-number-theory-v1",
            level="school", canonical_statement=statement, openmath_xml=xml,
            proof_strategy=reason,
            sketch_steps=[
                f"変数 {names} を{'自然数（0を含む）' if sort == 'Nat' else '整数'}として固定する。",
                "命題に書かれた仮定を保持し、両辺または整除条件を確認する。",
                reason,
                "得られた等式または整除条件が命題の結論と一致する。",
            ],
            lean_target=lean, lean_witness=proof,
            source_urls=["https://leanprover-community.github.io/mathematics_in_lean/C05_Elementary_Number_Theory.html"],
        ))

    for sort, ty, prefix in [("Nat", "ℕ", "nat"), ("Int", "ℤ", "int")]:
        plus = lambda x, y: nt(prefix + "_add", x, y)
        times = lambda x, y: nt(prefix + "_mul", x, y)
        z, o = literal(0, sort), literal(1, sort)
        cases = [
            ("add_comm", "a b", "a+b=b+a", plus(a,b), plus(b,a), "a+b=b+a", "exact add_comm a b"),
            ("add_assoc", "a b c", "(a+b)+c=a+(b+c)", plus(plus(a,b),c), plus(a,plus(b,c)), "(a+b)+c=a+(b+c)", "exact add_assoc a b c"),
            ("add_zero", "a", "a+0=a", plus(a,z), a, "a+0=a", "exact add_zero a"),
            ("mul_comm", "a b", "ab=ba", times(a,b), times(b,a), "a*b=b*a", "exact mul_comm a b"),
            ("mul_assoc", "a b c", "(ab)c=a(bc)", times(times(a,b),c), times(a,times(b,c)), "(a*b)*c=a*(b*c)", "exact mul_assoc a b c"),
            ("mul_one", "a", "a·1=a", times(a,o), a, "a*1=a", "exact mul_one a"),
            ("mul_zero", "a", "a·0=0", times(a,z), z, "a*0=0", "exact mul_zero a"),
            ("distributive", "a b c", "a(b+c)=ab+ac", times(a,plus(b,c)), plus(times(a,b),times(a,c)), "a*(b+c)=a*b+a*c", "exact mul_add a b c"),
            ("add_cancel", "a b c", "a+b=a+c ならば b=c", relation("implies",relation("eq",plus(a,b),plus(a,c)),relation("eq",b,c)), None, "a+b=a+c → b=c", "intro h\nexact add_left_cancel h"),
        ]
        for key,names,formula,lhs,rhs,prop,tactic in cases:
            body = lhs if rhs is None else relation("eq",lhs,rhs)
            add(prefix+"_"+key,names,sort,f"任意の{'自然数' if sort == 'Nat' else '整数'} {names} について、{formula}。",body,
                f"example ({names} : {ty}) : {prop}","by\n  "+tactic.replace("\n","\n  "),
                {"add_comm":"加法の交換法則を使う。","add_assoc":"加法の結合法則を使う。","add_zero":"0が加法の単位元であることを使う。","mul_comm":"乗法の交換法則を使う。","mul_assoc":"乗法の結合法則を使う。","mul_one":"1が乗法の単位元であることを使う。","mul_zero":"0との積が0になることを使う。","distributive":"乗法を加法に分配する。","add_cancel":"等式の両辺から共通の加数を消去する。"}[key])

    gcd=lambda x,y:nt("gcd",x,y)
    lcm=lambda x,y:nt("lcm",x,y)
    dvd=lambda x,y:nt("divides_nat",x,y)
    mul=lambda x,y:nt("nat_mul",x,y)
    plus=lambda x,y:nt("nat_add",x,y)
    z,o=literal(0),literal(1)
    entries = [
        ("gcd_self","a",relation("eq",gcd(a,a),a),"gcd(a,a)=a","Nat.gcd a a = a","exact Nat.gcd_self a","同じ数2個の最大公約数はその数である。"),
        ("gcd_one","a",relation("eq",gcd(a,o),o),"gcd(a,1)=1","Nat.gcd a 1 = 1","exact Nat.gcd_one_right a","1の自然数の約数は1だけなので最大公約数も1である。"),
        ("gcd_dvd_right","a b",dvd(gcd(a,b),b),"gcd(a,b) は b を割り切る","Nat.gcd a b ∣ b","exact Nat.gcd_dvd_right a b","最大公約数は両方の数の約数である。"),
        ("gcd_add_right","a b",relation("eq",gcd(a,plus(b,a)),gcd(a,b)),"gcd(a,b+a)=gcd(a,b)","Nat.gcd a (b+a) = Nat.gcd a b","exact Nat.gcd_add_self_right b a","共通の約数は一方に他方を加えても変わらない。"),
        ("lcm_comm","a b",relation("eq",lcm(a,b),lcm(b,a)),"lcm(a,b)=lcm(b,a)","Nat.lcm a b = Nat.lcm b a","exact Nat.lcm_comm a b","共通の倍数の条件は2つの数を交換しても同じである。"),
        ("lcm_self","a",relation("eq",lcm(a,a),a),"lcm(a,a)=a","Nat.lcm a a = a","exact Nat.lcm_self a","同じ数2個の最小公倍数はその数である。"),
        ("lcm_one","a",relation("eq",lcm(a,o),a),"lcm(a,1)=a","Nat.lcm a 1 = a","exact Nat.lcm_one_right a","1の倍数条件は自然数全体なので共通の倍数はaの倍数である。"),
        ("dvd_lcm_left","a b",dvd(a,lcm(a,b)),"a は lcm(a,b) を割り切る","a ∣ Nat.lcm a b","exact Nat.dvd_lcm_left a b","最小公倍数はそれぞれの数の倍数である。"),
        ("dvd_lcm_right","a b",dvd(b,lcm(a,b)),"b は lcm(a,b) を割り切る","b ∣ Nat.lcm a b","exact Nat.dvd_lcm_right a b","最小公倍数はそれぞれの数の倍数である。"),
        ("gcd_lcm_product","a b",relation("eq",mul(gcd(a,b),lcm(a,b)),mul(a,b)),"gcd(a,b)lcm(a,b)=ab","Nat.gcd a b * Nat.lcm a b = a*b","exact Nat.gcd_mul_lcm a b","最大公約数と最小公倍数の積の公式を使う。"),
        ("dvd_zero","a",dvd(a,z),"a は 0 を割り切る","a ∣ 0","exact dvd_zero a","0=a·0 を整除の定義に代入する。"),
        ("one_dvd","a",dvd(o,a),"1 は a を割り切る","1 ∣ a","exact one_dvd a","a=1·a を整除の定義に代入する。"),
        ("dvd_add","a b c",relation("implies",relation("and",dvd(a,b),dvd(a,c)),dvd(a,plus(b,c))),"a|b かつ a|c ならば a|(b+c)","a ∣ b ∧ a ∣ c → a ∣ b+c","intro h\nexact dvd_add h.1 h.2","bとcをaの倍数として表し、その和もaの倍数として表す。"),
        ("common_divisor_gcd","a b c",relation("implies",relation("and",dvd(a,b),dvd(a,c)),dvd(a,gcd(b,c))),"a|b かつ a|c ならば a|gcd(b,c)","a ∣ b ∧ a ∣ c → a ∣ Nat.gcd b c","intro h\nexact Nat.dvd_gcd h.1 h.2","最大公約数の共通約数に関する普遍性を使う。"),
        ("dvd_antisymm","a b",relation("implies",relation("and",dvd(a,b),dvd(b,a)),relation("eq",a,b)),"a|b かつ b|a ならば a=b","a ∣ b ∧ b ∣ a → a=b","intro h\nexact Nat.dvd_antisymm h.1 h.2","自然数の整除関係の反対称性を使う。"),
        ("dvd_mul_left","a b",dvd(a,mul(a,b)),"a は ab を割り切る","a ∣ a*b","exact dvd_mul_right a b","商としてbを取り、整除の定義を満たす。"),
        ("gcd_mul_right","a b",relation("eq",gcd(a,mul(a,b)),a),"gcd(a,ab)=a","Nat.gcd a (a*b)=a","exact Nat.gcd_eq_left (dvd_mul_right a b)","aがabを割り切るので共通約数の最大のものはaになる。"),
        ("lcm_mul_right","a b",relation("eq",lcm(a,mul(a,b)),mul(a,b)),"lcm(a,ab)=ab","Nat.lcm a (a*b)=a*b","exact Nat.lcm_eq_right (dvd_mul_right a b)","abがaの倍数なので共通の倍数の最小のものはabになる。"),
    ]
    for key,names,xml,formula,prop,tactic,reason in entries:
        add(key,names,"Nat",f"任意の自然数 {names} について、{formula}。",xml,
            f"example ({names} : ℕ) : {prop}","by\n  "+tactic.replace("\n","\n  "),reason)
    return result
