package time_check_recognition

import (
	"encoding/json"
	"fmt"
	"testing"
	"time"

	"maa-yys-agent/actions/time_check"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

func mustParseTime(t *testing.T, value string) time.Time {
	t.Helper()
	parsed, err := time.Parse("2006-01-02 15:04:05", value)
	if err != nil {
		t.Fatalf("解析时间 %s 失败: %v", value, err)
	}
	return parsed
}

func mustParseParams(t *testing.T, raw string) TimeCheckRecognitionParams {
	t.Helper()
	params := TimeCheckRecognitionParams{Mode: "in"}
	if err := json.Unmarshal([]byte(raw), &params); err != nil {
		t.Fatalf("解析参数 %s 失败: %v", raw, err)
	}
	return params
}

func TestEvaluate(t *testing.T) {
	// 2025-01-08 是星期三，week 值为 3
	cases := []struct {
		name string
		now  string
		raw  string
		want bool
	}{
		{"同一天范围内", "2025-01-08 15:30:00", `{"start":"12:00","end":"23:00"}`, true},
		{"同一天范围外", "2025-01-08 15:30:00", `{"start":"16:00","end":"23:00"}`, false},
		{"开始时间含边界", "2025-01-08 15:30:00", `{"start":"15:30","end":"16:00"}`, true},
		{"结束时间含边界", "2025-01-08 15:30:00", `{"start":"15:00","end":"15:30"}`, true},
		{"跨天范围内", "2025-01-08 02:00:00", `{"start":"23:00","end":"06:00"}`, true},
		{"跨天范围外", "2025-01-08 15:30:00", `{"start":"23:00","end":"06:00"}`, false},
		{"省略前导零", "2025-01-08 06:30:00", `{"start":"6:00","end":"7:00"}`, true},
		{"秒级时间格式", "2025-01-08 15:30:00", `{"start":"15:29:59","end":"15:30:01"}`, true},
		{"mode=out 范围内取反", "2025-01-08 15:30:00", `{"start":"12:00","end":"23:00","mode":"out"}`, false},
		{"mode=out 范围外为真", "2025-01-08 15:30:00", `{"start":"16:00","end":"23:00","mode":"out"}`, true},
		{"date 规则命中", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"date","value":"2025-01-08"}}`, true},
		{"date 规则未命中", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"date","value":"2025-01-09"}}`, false},
		{"dates 规则命中", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"dates","value":["2025-01-07","2025-01-08"]}}`, true},
		{"dates 规则未命中", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"dates","value":["2025-01-09"]}}`, false},
		{"week 规则命中", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"week","value":[3]}}`, true},
		{"week 规则未命中", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"week","value":[6,7]}}`, false},
		{"week 周日按 7 计算", "2025-01-12 15:30:00", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"week","value":[7]}}`, true},
		{"month_day 规则命中", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"month_day","value":[8]}}`, true},
		{"month_day 规则未命中", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"month_day","value":[9]}}`, false},
		{"日期规则未命中且 mode=out 为真", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59","mode":"out","date_rule":{"type":"date","value":"2025-01-09"}}`, true},
		{"type=none 不过滤日期", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"none"}}`, true},
		{"未提供日期规则", "2025-01-08 15:30:00", `{"start":"00:00","end":"23:59:59"}`, true},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := evaluate(mustParseParams(t, tc.raw), mustParseTime(t, tc.now))
			if err != nil {
				t.Fatalf("evaluate() 返回错误: %v", err)
			}
			if got != tc.want {
				t.Fatalf("evaluate(%s) = %v, want %v", tc.raw, got, tc.want)
			}
		})
	}
}

func TestEvaluateWithInvalidParams(t *testing.T) {
	now := mustParseTime(t, "2025-01-08 15:30:00")

	cases := []struct {
		name string
		raw  string
	}{
		{"缺少 start", `{"end":"23:00"}`},
		{"缺少 end", `{"start":"12:00"}`},
		{"缺少 start 与 end", `{}`},
		{"start 非法", `{"start":"abc","end":"23:00"}`},
		{"end 非法", `{"start":"12:00","end":"24:99"}`},
		{"未知模式", `{"start":"12:00","end":"23:00","mode":"xx"}`},
		{"mode 显式为空", `{"start":"12:00","end":"23:00","mode":""}`},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if _, err := evaluate(mustParseParams(t, tc.raw), now); err == nil {
				t.Fatalf("evaluate(%s) 未返回错误", tc.raw)
			}
		})
	}
}

func TestRun(t *testing.T) {
	runner := &TimeCheckRecognition{}

	t.Run("覆盖全天的时间范围内识别成功", func(t *testing.T) {
		result, ok := runner.Run(nil, &maa.CustomRecognitionArg{
			CustomRecognitionParam: `{"start":"00:00","end":"23:59:59"}`,
		})
		if !ok {
			t.Fatal("识别失败，期望识别成功")
		}
		if result == nil {
			t.Fatal("识别成功时结果不应为 nil")
		}
		if result.Box != (maa.Rect{0, 0, 0, 0}) {
			t.Fatalf("识别结果 Box = %+v, want 空框", result.Box)
		}
	})

	t.Run("日期规则未命中时识别失败", func(t *testing.T) {
		result, ok := runner.Run(nil, &maa.CustomRecognitionArg{
			CustomRecognitionParam: `{"start":"00:00","end":"23:59:59","date_rule":{"type":"date","value":"1970-01-01"}}`,
		})
		if ok {
			t.Fatal("识别成功，期望识别失败")
		}
		if result != nil {
			t.Fatalf("识别失败时结果应为 nil, got %+v", result)
		}
	})

	t.Run("参数非法时识别失败", func(t *testing.T) {
		for _, raw := range []string{`not-json`, `{}`, `{"start":"abc","end":"23:00"}`, `{"start":"12:00","end":"23:00","mode":"xx"}`} {
			if _, ok := runner.Run(nil, &maa.CustomRecognitionArg{CustomRecognitionParam: raw}); ok {
				t.Fatalf("参数 %s 识别成功，期望识别失败", raw)
			}
		}
	})

	t.Run("空参数时识别失败", func(t *testing.T) {
		if _, ok := runner.Run(nil, nil); ok {
			t.Fatal("空参数识别成功，期望识别失败")
		}
	})
}

// TestMatchesTimeCheckAction 保证识别器与 TimeCheck 自定义动作的判断结果完全一致
func TestMatchesTimeCheckAction(t *testing.T) {
	format := func(offset time.Duration) string {
		return time.Now().Add(offset).Format("15:04")
	}

	cases := []struct {
		name string
		raw  string
	}{
		{"覆盖全天", `{"start":"00:00","end":"23:59:59"}`},
		{"当前时间之后", fmt.Sprintf(`{"start":%q,"end":%q}`, format(time.Hour), format(2*time.Hour))},
		{"当前时间前后", fmt.Sprintf(`{"start":%q,"end":%q}`, format(-time.Hour), format(time.Hour))},
		{"跨天范围", `{"start":"23:00","end":"06:00"}`},
		{"起止相同", `{"start":"12:00","end":"12:00"}`},
		{"秒级时间", `{"start":"00:00:00","end":"23:59:59"}`},
		{"mode=out", `{"start":"00:00","end":"23:59:59","mode":"out"}`},
		{"日期未命中", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"date","value":"1970-01-01"}}`},
		{"日期未命中 mode=out", `{"start":"00:00","end":"23:59:59","mode":"out","date_rule":{"type":"date","value":"1970-01-01"}}`},
		{"week 覆盖一周", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"week","value":[1,2,3,4,5,6,7]}}`},
		{"month_day 未命中", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"month_day","value":[32]}}`},
		{"未知日期规则类型", `{"start":"00:00","end":"23:59:59","date_rule":{"type":"unknown"}}`},
		{"缺少 start 与 end", `{}`},
		{"缺少 end", `{"start":"12:00"}`},
		{"时间非法", `{"start":"abc","end":"23:00"}`},
		{"未知模式", `{"start":"00:00","end":"23:59:59","mode":"xx"}`},
	}

	action := &time_check.TimeCheck{}
	runner := &TimeCheckRecognition{}
	succeeded := 0

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			want := action.Run(nil, &maa.CustomActionArg{CustomActionParam: tc.raw})
			_, got := runner.Run(nil, &maa.CustomRecognitionArg{CustomRecognitionParam: tc.raw})
			if got != want {
				t.Fatalf("TimeCheckRecognition = %v, TimeCheck 动作 = %v, 参数 %s", got, want, tc.raw)
			}
			if want {
				succeeded++
			}
		})
	}

	if succeeded == 0 || succeeded == len(cases) {
		t.Fatalf("对照用例未覆盖成功/失败两种结果: 成功 %d / 共 %d", succeeded, len(cases))
	}
}
