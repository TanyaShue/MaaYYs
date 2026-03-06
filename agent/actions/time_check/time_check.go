package time_check

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type TimeCheck struct{}

type TimeCheckParams struct {
	Start    string `json:"start"`
	End      string `json:"end"`
	Mode     string `json:"mode"`
	DateRule struct {
		Type  string      `json:"type"`
		Value interface{} `json:"value"`
	} `json:"date_rule"`
}

// Run 检查当前系统时间是否在指定范围内
func (a *TimeCheck) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：时间 + 日期范围检查")

	params := TimeCheckParams{Mode: "in"}
	if arg.CustomActionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
			fmt.Printf("参数JSON解析失败: %v\n", err)
			return false
		}
	}

	if params.Start == "" || params.End == "" {
		fmt.Println("错误：必须提供 start 和 end 时间")
		return false
	}

	now := time.Now()
	nowTime := now.Format("15:04:05")
	today := now.Format("2006-01-02")

	fmt.Printf("当前时间: %s %s\n", today, nowTime)
	fmt.Printf("时间范围: %s - %s, 模式: %s\n", params.Start, params.End, params.Mode)

	// 解析时间
	startTime, err := time.Parse("15:04", params.Start)
	if err != nil {
		startTime, err = time.Parse("15:04:05", params.Start)
		if err != nil {
			fmt.Printf("时间格式错误: %v\n", err)
			return false
		}
	}

	endTime, err := time.Parse("15:04", params.End)
	if err != nil {
		endTime, err = time.Parse("15:04:05", params.End)
		if err != nil {
			fmt.Printf("时间格式错误: %v\n", err)
			return false
		}
	}

	// 检查日期规则
	dateOK := a.checkDateRule(params.DateRule, now)
	fmt.Printf("日期规则检查结果: %v\n", dateOK)

	if !dateOK {
		if params.Mode == "in" {
			return false
		}
		return true
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
	if params.Mode == "in" {
		result = isInRange
	} else if params.Mode == "out" {
		result = !isInRange
	} else {
		fmt.Printf("未知模式 '%s'\n", params.Mode)
		return false
	}

	fmt.Printf("最终结果: %v\n", result)
	return result
}

func (a *TimeCheck) checkDateRule(rule struct {
	Type  string      `json:"type"`
	Value interface{} `json:"value"`
}, now time.Time) bool {
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