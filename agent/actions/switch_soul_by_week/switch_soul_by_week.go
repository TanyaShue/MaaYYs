package switch_soul_by_week

import (
	"bytes"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

const (
	// 复用「切换御魂」使用的装备御魂流程。
	soulTaskName      = "装备御魂"
	soulGroupNodeName = "装备御魂-识别目标分组"
	soulTeamNodeName  = "装备御魂-识别队伍名称"
)

// SwitchSoulByWeek 按当前星期选择御魂预设并装备御魂。
//
// 参数格式固定为 8 个键：default 与 monday~sunday，每个键是 {group_name, team_name}。
// 未传入的键视为没有配置。
//
//	{
//	  "default": {"group_name": "御魂", "team_name": "魂土"},
//	  "monday":  {"group_name": "御魂", "team_name": "魂土"},
//	  "tuesday": {"group_name": "御魂", "team_name": "魂十"}
//	}
//
// 取值顺序：当天配置 → default → 周一 → 周二 … → 周日。
type SwitchSoulByWeek struct{}

// SwitchSoulByWeekParams 星期到御魂预设的映射，未传入的键为 nil。
type SwitchSoulByWeekParams struct {
	Default   *SoulPreset `json:"default"`
	Monday    *SoulPreset `json:"monday"`
	Tuesday   *SoulPreset `json:"tuesday"`
	Wednesday *SoulPreset `json:"wednesday"`
	Thursday  *SoulPreset `json:"thursday"`
	Friday    *SoulPreset `json:"friday"`
	Saturday  *SoulPreset `json:"saturday"`
	Sunday    *SoulPreset `json:"sunday"`
}

// SoulPreset 一组御魂预设：分组名 + 队伍名。
type SoulPreset struct {
	GroupName string `json:"group_name"`
	TeamName  string `json:"team_name"`
}

// weekdayOrder 回退顺序：周一 → 周二 → … → 周日。
var weekdayOrder = []time.Weekday{
	time.Monday,
	time.Tuesday,
	time.Wednesday,
	time.Thursday,
	time.Friday,
	time.Saturday,
	time.Sunday,
}

var weekdayLabels = map[time.Weekday]string{
	time.Monday:    "周一",
	time.Tuesday:   "周二",
	time.Wednesday: "周三",
	time.Thursday:  "周四",
	time.Friday:    "周五",
	time.Saturday:  "周六",
	time.Sunday:    "周日",
}

// Run 按当前星期决定分组和队伍，然后执行装备御魂任务。
func (a *SwitchSoulByWeek) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	rawParam := ""
	if arg != nil {
		rawParam = arg.CustomActionParam
	}

	params, err := parseParams(rawParam)
	if err != nil {
		fmt.Printf("按周切换御魂参数解析失败: %v\n", err)
		return false
	}

	now := time.Now()
	preset, source, ok := params.resolve(now.Weekday())
	if !ok {
		fmt.Printf("按周切换御魂失败：今天%s没有任何可用的御魂配置，请至少传入当天、default 或某一天的 group_name 与 team_name\n",
			weekdayLabels[now.Weekday()])
		return false
	}

	fmt.Printf("按周切换御魂：今天%s，使用分组 %s、队伍 %s（%s）\n",
		weekdayLabels[now.Weekday()], preset.GroupName, preset.TeamName, source)

	result, err := ctx.RunTask(soulTaskName, map[string]any{
		soulGroupNodeName: map[string]any{
			"expected": preset.GroupName,
		},
		soulTeamNodeName: map[string]any{
			"expected": preset.TeamName,
		},
	})
	if err != nil {
		fmt.Printf("执行任务 %s 失败: %v\n", soulTaskName, err)
		return false
	}

	return result != nil
}

// parseParams 按固定格式解析参数：只允许 default 与 monday~sunday 八个键。
func parseParams(raw string) (*SwitchSoulByWeekParams, error) {
	params := &SwitchSoulByWeekParams{}

	raw = strings.TrimSpace(raw)
	if raw == "" {
		return params, nil
	}

	decoder := json.NewDecoder(bytes.NewReader([]byte(raw)))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(params); err != nil {
		return nil, fmt.Errorf("参数必须是仅含 default、monday~sunday 的 JSON 对象: %w", err)
	}

	params.normalize()
	return params, nil
}

// preset 返回指定星期的配置，未传入时为 nil。
func (p *SwitchSoulByWeekParams) preset(weekday time.Weekday) *SoulPreset {
	switch weekday {
	case time.Monday:
		return p.Monday
	case time.Tuesday:
		return p.Tuesday
	case time.Wednesday:
		return p.Wednesday
	case time.Thursday:
		return p.Thursday
	case time.Friday:
		return p.Friday
	case time.Saturday:
		return p.Saturday
	default:
		return p.Sunday
	}
}

// resolve 按 当天 → default → 周一…周日 的顺序依次补全分组与队伍。
func (p *SwitchSoulByWeekParams) resolve(today time.Weekday) (SoulPreset, string, bool) {
	resolved := SoulPreset{}
	groupSource, teamSource := "", ""

	apply := func(preset *SoulPreset, source string) bool {
		if preset == nil {
			return resolved.GroupName != "" && resolved.TeamName != ""
		}
		if resolved.GroupName == "" && preset.GroupName != "" {
			resolved.GroupName = preset.GroupName
			groupSource = source
		}
		if resolved.TeamName == "" && preset.TeamName != "" {
			resolved.TeamName = preset.TeamName
			teamSource = source
		}
		return resolved.GroupName != "" && resolved.TeamName != ""
	}

	if apply(p.preset(today), weekdayLabels[today]+"配置") {
		return resolved, sourceOf(groupSource, teamSource), true
	}
	if apply(p.Default, "默认配置") {
		return resolved, sourceOf(groupSource, teamSource), true
	}
	for _, weekday := range weekdayOrder {
		if apply(p.preset(weekday), weekdayLabels[weekday]+"配置") {
			return resolved, sourceOf(groupSource, teamSource), true
		}
	}

	return SoulPreset{}, "", false
}

func sourceOf(groupSource, teamSource string) string {
	return fmt.Sprintf("分组来自%s，队伍来自%s", groupSource, teamSource)
}

// normalize 清理首尾空白，并把 group_name、team_name 都为空的配置视为未传入。
func (p *SwitchSoulByWeekParams) normalize() {
	p.Default = normalizedPreset(p.Default)
	p.Monday = normalizedPreset(p.Monday)
	p.Tuesday = normalizedPreset(p.Tuesday)
	p.Wednesday = normalizedPreset(p.Wednesday)
	p.Thursday = normalizedPreset(p.Thursday)
	p.Friday = normalizedPreset(p.Friday)
	p.Saturday = normalizedPreset(p.Saturday)
	p.Sunday = normalizedPreset(p.Sunday)
}

func normalizedPreset(preset *SoulPreset) *SoulPreset {
	if preset == nil {
		return nil
	}
	preset.GroupName = strings.TrimSpace(preset.GroupName)
	preset.TeamName = strings.TrimSpace(preset.TeamName)
	if preset.GroupName == "" && preset.TeamName == "" {
		return nil
	}
	return preset
}
