import Mathlib

open scoped BigOperators

-- manifest card: typed_finite_graph_v1_handshaking
example : ∀ {V : Type*} [Fintype V] (G : SimpleGraph V) [DecidableRel G.Adj],
    (∑ v, G.degree v) = 2 * G.edgeFinset.card := by
  intro V _ G _
  exact G.sum_degrees_eq_twice_card_edges

-- manifest card: typed_finite_graph_v1_tree_edge_count
example : ∀ {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V) [DecidableRel G.Adj],
    G.IsTree → G.edgeFinset.card + 1 = Fintype.card V := by
  intro V _ _ G _ hG
  exact hG.card_edgeFinset

-- manifest card: typed_finite_graph_v1_tree_connected
example : ∀ {V : Type*} (G : SimpleGraph V), G.IsTree → G.Connected := by
  intro V G hG
  exact hG.connected

-- manifest card: typed_finite_graph_v1_tree_bipartite
example : ∀ {V : Type*} (G : SimpleGraph V), G.IsTree → G.IsBipartite := by
  intro V G hG
  exact hG.isBipartite

-- manifest card: typed_finite_graph_v1_euler_trail_odd_degree_necessity
example : ∀ {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V) [DecidableRel G.Adj]
    {u v : V} (p : G.Walk u v), p.IsEulerian →
      Fintype.card {w | Odd (G.degree w)} = 0 ∨ Fintype.card {w | Odd (G.degree w)} = 2 := by
  intro V _ _ G _ u v p hp
  exact hp.card_odd_degree
