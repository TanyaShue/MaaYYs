package main

import (
	"math"
	"testing"
)

func sampleSoul() inputSoul {
	var soul inputSoul
	soul.Type = "元兴寺"
	soul.Position = 4
	soul.Level = 0
	soul.Attributes.Main = inputAttribute{Name: "防御加成", Value: "10.00%"}
	soul.Attributes.Subs = []inputAttribute{{Name: "防御", Value: "4.64"}, {Name: "攻击", Value: "25.14"}}
	return soul
}

func TestEnumerateStatesProbabilityAndRollBounds(t *testing.T) {
	states := enumerateStates(sampleSoul())
	total := 0.0
	maxSpeedRolls := 0
	for _, state := range states {
		total += state.Prob
		for _, attr := range state.Attrs {
			if attr.Name == "速度" && attr.FutureRolls > maxSpeedRolls {
				maxSpeedRolls = attr.FutureRolls
			}
		}
	}
	if math.Abs(total-1) > 1e-12 {
		t.Fatalf("状态概率和 = %.15f, want 1", total)
	}
	if maxSpeedRolls != 5 {
		t.Fatalf("速度最大roll数 = %d, want 5", maxSpeedRolls)
	}
}

func TestTwoLegRollCanReinforceOrAdd(t *testing.T) {
	soul := sampleSoul()
	soul.Level = 12
	states := enumerateStates(soul)
	// At +12 -> +15, both existing attributes and each of the eight other
	// non-main attributes are possible: 10 equally likely choices in total.
	if len(states) != 10 {
		t.Fatalf("状态数 = %d, want 10", len(states))
	}
	for _, state := range states {
		if math.Abs(state.Prob-0.1) > 1e-12 {
			t.Fatalf("单次选择概率 = %g, want 0.1", state.Prob)
		}
	}
}

func TestSampleCannotReachExtremeThreshold(t *testing.T) {
	soul := sampleSoul()
	r := route{Name: "极限速度", Attrs: []string{"速度"}, Weights: map[string]float64{"速度": 1}, TopN: 1, Threshold: 4.5}
	states := enumerateStates(soul)
	if got := probabilityAtLeast(states, soul, r, 4.5); got <= 0 || got >= 1e-3 {
		t.Fatalf("达成4.5概率 = %g, want a small non-zero probability", got)
	}
	_, _, maximum := scoreMoments(states, soul, r)
	if math.Abs(maximum-5) > 1e-12 {
		t.Fatalf("理论最高分 = %g, want 5", maximum)
	}
}

func TestFourLegOneStepIsUniform(t *testing.T) {
	soul := sampleSoul()
	soul.Level = 12
	soul.Attributes.Subs = []inputAttribute{{Name: "防御", Value: "4.64"}, {Name: "攻击", Value: "25.14"}, {Name: "速度", Value: "2.70"}, {Name: "生命", Value: "100"}}
	states := enumerateStates(soul)
	if len(states) != 4 {
		t.Fatalf("状态数 = %d, want 4", len(states))
	}
	for _, state := range states {
		if math.Abs(state.Prob-.25) > 1e-12 {
			t.Fatalf("单条强化概率 = %g, want 0.25", state.Prob)
		}
	}
}

func TestDeterministicThresholdUsesGreaterOrEqual(t *testing.T) {
	soul := sampleSoul()
	soul.Level = 15
	soul.Attributes.Subs = []inputAttribute{{Name: "速度", Value: "3.00"}, {Name: "攻击", Value: "25.14"}}
	r := route{Attrs: []string{"速度"}, Weights: map[string]float64{"速度": 1}}
	if got := probabilityAtLeast(enumerateStates(soul), soul, r, 1); got != 1 {
		t.Fatalf("确定分恰好达标概率 = %g, want 1", got)
	}
}
