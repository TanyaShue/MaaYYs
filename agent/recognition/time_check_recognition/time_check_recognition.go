package time_check_recognition

import (
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

// TimeCheckRecognition 时间 + 日期范围检查识别器。
//
// 参数与 actions/time_check 的 TimeCheck 自定义动作完全一致，判断逻辑也保持一致：
// 当前系统时间（可附加日期规则）满足条件时识别成功（返回 true），否则识别失败（返回 false）。
// 两者的一致性由 time_check_recognition_test.go 的对照测试保证。
type TimeCheckRecognition struct{}

// TimeCheckRecognitionParams 识别参数
type TimeCheckRecognitionParams struct {
	Start    string   `json:"start"`
	End      string   `json:"end"`
	Mode     string   `json:"mode"`
	DateRule DateRule `json:"date_rule"`
}

// DateRule 可选的日期过滤规则，Type 支持 none/date/dates/month_day/week
type DateRule struct {
	Type  string      `json:"type"`
	Value interface{} `json:"value"`
}

// 确保实现 CustomRecognitionRunner 接口
var _ maa.CustomRecognitionRunner = &TimeCheckRecognition{}

// Run 检查当前系统时间是否在指定范围内
// 在范围内返回识别成功，不在范围内返回识别失败
func (r *TimeCheckRecognition) Run(ctx *maa.Context, arg *maa.CustomRecognitionArg) (*maa.CustomRecognitionResult, bool) {
	fmt.Println("开始执行自定义识别：时间 + 日期范围检查")

	params := TimeCheckRecognitionParams{Mode: "in"}
	if arg != nil && arg.CustomRecognitionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomRecognitionParam), &params); err != nil {
			fmt.Printf("TimeCheckRecognition: 参数JSON解析失败: %v\n", err)
			return nil, false
		}
	}

	matched, err := evaluate(params, time.Now())
	if err != nil {
		fmt.Printf("TimeCheckRecognition: %v\n", err)
		return nil, false
	}

	if !matched {
		return nil, false
	}

	// 时间检查不依赖画面，返回空的结果表示识别成功
	return &maa.CustomRecognitionResult{Box: maa.Rect{0, 0, 0, 0}}, true
}

// evaluate 判断 now 是否满足参数条件，判断过程与 TimeCheck 自定义动作一致。
// now 由调用方传入，便于测试。
func evaluate(params TimeCheckRecognitionParams, now time.Time) (bool, error) {
	if params.Start == "" || params.End == "" {
		return false, errors.New("必须提供 start 和 end 时间")
	}

	nowTime := now.Format("15:04:05")
	today := now.Format("2006-01-02")

	fmt.Printf("当前时间: %s %s\n", today, nowTime)
	fmt.Printf("时间范围: %s - %s, 模式: %s\n", params.Start, params.End, params.Mode)

	// 解析时间
	startTime, err := parseClock(params.Start)
	if err != nil {
		return false, fmt.Errorf("时间格式错误: %w", err)
	}

	endTime, err := parseClock(params.End)
	if err != nil {
		return false, fmt.Errorf("时间格式错误: %w", err)
	}

	// 检查日期规则
	dateOK := checkDateRule(params.DateRule, now)
	fmt.Printf("日期规则检查结果: %v\n", dateOK)

	if !dateOK {
		if params.Mode == "in" {
			return false, nil
		}
		return true, nil
	}

	// 解析当前时间
	nowTimeParsed, _ := time.Parse("15:04:05", nowTime)

	// 时间范围判断
	isInRange := false
	if startTime.Before(endTime) {
		// 同一天
		if (nowTimeParsed.After(startTime) || nowTimeParsed.Equal(startTime)) &&
			(nowTimeParsed.Before(endTime) || nowTimeParsed.Equal(endTime)) {
			isInRange = true
		}
	} else {
		// 跨天
		if nowTimeParsed.After(startTime) || nowTimeParsed.Before(endTime) {
			isInRange = true
		}
	}

	// 模式判断
	var result bool
	switch params.Mode {
	case "in":
		result = isInRange
	case "out":
		result = !isInRange
	default:
		return false, fmt.Errorf("未知模式 '%s'", params.Mode)
	}

	fmt.Printf("最终结果: %v\n", result)
	return result, nil
}

// parseClock 依次尝试 HH:mm 与 HH:mm:ss 两种格式
func parseClock(value string) (time.Time, error) {
	parsed, err := time.Parse("15:04", value)
	if err == nil {
		return parsed, nil
	}
	return time.Parse("15:04:05", value)
}

// checkDateRule 检查日期规则，未配置或未知规则时不限制日期
func checkDateRule(rule DateRule, now time.Time) bool {
	if rule.Type == "" || rule.Type == "none" {
		return true
	}

	today := now.Format("2006-01-02")

	switch rule.Type {
	case "date":
		if str, ok := rule.Value.(string); ok {
			return today == str
		}
	case "dates":
		if arr, ok := rule.Value.([]interface{}); ok {
			for _, d := range arr {
				if str, ok := d.(string); ok && str == today {
					return true
				}
			}
			return false
		}
	case "month_day":
		if arr, ok := rule.Value.([]interface{}); ok {
			day := now.Day()
			for _, d := range arr {
				if v, ok := d.(float64); ok && int(v) == day {
					return true
				}
			}
			return false
		}
	case "week":
		if arr, ok := rule.Value.([]interface{}); ok {
			weekday := int(now.Weekday())
			if weekday == 0 {
				weekday = 7 // 将周日从0改为7
			}
			for _, d := range arr {
				if v, ok := d.(float64); ok && int(v) == weekday {
					return true
				}
			}
			return false
		}
	}

	return true
}
