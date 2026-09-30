package guess

import "testing"

func TestPickBet(t *testing.T) {
	tests := []struct {
		name                  string
		leftCount, rightCount int
		leftOK, rightOK       bool
		wantTask, wantWinner  string
	}{
		{name: "左边人多", leftCount: 7, rightCount: 3, leftOK: true, rightOK: true, wantTask: taskBetLeft, wantWinner: "左边"},
		{name: "右边人多", leftCount: 3, rightCount: 7, leftOK: true, rightOK: true, wantTask: taskBetRight, wantWinner: "右边"},
		{name: "人数相同押左边", leftCount: 4, rightCount: 4, leftOK: true, rightOK: true, wantTask: taskBetLeft, wantWinner: "左边"},
		{name: "左边为0", leftCount: 0, rightCount: 6, leftOK: true, rightOK: true, wantTask: taskBetRight, wantWinner: "右边"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			task, winner := pickBet(tt.leftCount, tt.leftOK, tt.rightCount, tt.rightOK)
			if task != tt.wantTask || winner != tt.wantWinner {
				t.Errorf("pickBet() = (%q, %q), want (%q, %q)", task, winner, tt.wantTask, tt.wantWinner)
			}
		})
	}
}

// TestPickBetFallsBackToRandom 识别失败时必须仍然给出一个合法的押注目标。
func TestPickBetFallsBackToRandom(t *testing.T) {
	seen := map[string]bool{}
	for range 200 {
		task, winner := pickBet(0, false, 0, false)
		if (task == taskBetLeft && winner != "左边") || (task == taskBetRight && winner != "右边") {
			t.Fatalf("pickBet() 返回了不匹配的组合: (%q, %q)", task, winner)
		}
		if task != taskBetLeft && task != taskBetRight {
			t.Fatalf("pickBet() 返回了未知任务: %q", task)
		}
		seen[task] = true
	}
	if len(seen) != 2 {
		t.Errorf("识别失败时应随机选择两边, 实际只出现了 %v", seen)
	}
}

func TestDescribeCount(t *testing.T) {
	if got := describeCount(0, "", false); got != "失败" {
		t.Errorf("describeCount(失败) = %q, want %q", got, "失败")
	}
	if got := describeCount(7, "7", true); got != "7" {
		t.Errorf("describeCount(7) = %q, want %q", got, "7")
	}
	if got := describeCount(12, "12人", true); got != `12 (OCR原始文本: "12人")` {
		t.Errorf("describeCount(12人) = %q", got)
	}
}
