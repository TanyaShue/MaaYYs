package auto_foster

import "testing"

func TestParseRewardText(t *testing.T) {
	a := &AutoFoster{}
	tests := []struct {
		name      string
		text      string
		wantType  string
		wantValue int
	}{
		{name: "standard", text: "勾玉+67", wantType: "勾玉", wantValue: 67},
		{name: "spaces", text: "体力 + 130", wantType: "体力", wantValue: 130},
		{name: "full-width plus", text: "勾玉＋76", wantType: "勾玉", wantValue: 76},
		{name: "no plus", text: "勾玉 67", wantType: "勾玉", wantValue: 67},
		{name: "empty", text: "", wantType: "", wantValue: 0},
		{name: "invalid", text: "没有奖励", wantType: "", wantValue: 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotType, gotValue := a.parseRewardText(tt.text)
			if gotType != tt.wantType || gotValue != tt.wantValue {
				t.Fatalf("parseRewardText(%q) = (%q, %d), want (%q, %d)", tt.text, gotType, gotValue, tt.wantType, tt.wantValue)
			}
		})
	}
}

func TestGetDirectSelectThreshold(t *testing.T) {
	tests := []struct {
		name            string
		prioritizedType string
		override        int
		want            int
	}{
		{name: "magatama requires parameter", prioritizedType: "勾玉", want: 0},
		{name: "stamina default", prioritizedType: "体力", want: DefaultStaminaDirectThreshold},
		{name: "magatama override", prioritizedType: "勾玉", override: 67, want: 67},
		{name: "stamina ignores override", prioritizedType: "体力", override: 67, want: DefaultStaminaDirectThreshold},
		{name: "invalid magatama override", prioritizedType: "勾玉", override: -1, want: 0},
		{name: "unknown type", prioritizedType: "金币", want: 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := getDirectSelectThreshold(tt.prioritizedType, tt.override); got != tt.want {
				t.Fatalf("getDirectSelectThreshold(%q, %d) = %d, want %d", tt.prioritizedType, tt.override, got, tt.want)
			}
		})
	}
}

func TestShouldDirectSelect(t *testing.T) {
	tests := []struct {
		name            string
		reward          RewardInfo
		prioritizedType string
		threshold       int
		want            bool
	}{
		{name: "at threshold", reward: RewardInfo{YieldType: "勾玉", YieldValue: 67}, prioritizedType: "勾玉", threshold: 67, want: true},
		{name: "above threshold", reward: RewardInfo{YieldType: "勾玉", YieldValue: 76}, prioritizedType: "勾玉", threshold: 67, want: true},
		{name: "below threshold", reward: RewardInfo{YieldType: "勾玉", YieldValue: 66}, prioritizedType: "勾玉", threshold: 67, want: false},
		{name: "other type", reward: RewardInfo{YieldType: "体力", YieldValue: 150}, prioritizedType: "勾玉", threshold: 67, want: false},
		{name: "disabled", reward: RewardInfo{YieldType: "勾玉", YieldValue: 76}, prioritizedType: "勾玉", threshold: 0, want: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := shouldDirectSelect(tt.reward, tt.prioritizedType, tt.threshold); got != tt.want {
				t.Fatalf("shouldDirectSelect(%+v, %q, %d) = %v, want %v", tt.reward, tt.prioritizedType, tt.threshold, got, tt.want)
			}
		})
	}
}
