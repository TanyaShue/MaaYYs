package switch_soul_by_week

import (
	"testing"
	"time"
)

func TestResolve(t *testing.T) {
	weekly := &SwitchSoulByWeekParams{
		Monday:  &SoulPreset{GroupName: "御魂", TeamName: "魂土"},
		Tuesday: &SoulPreset{GroupName: "御魂", TeamName: "魂十"},
	}
	withDefault := &SwitchSoulByWeekParams{
		Default:  &SoulPreset{GroupName: "御魂", TeamName: "魂王"},
		Monday:   &SoulPreset{GroupName: "御魂", TeamName: "魂土"},
		Tuesday:  &SoulPreset{GroupName: "御魂", TeamName: "魂十"},
		Saturday: &SoulPreset{GroupName: "御魂", TeamName: "魂王"},
	}

	tests := []struct {
		name       string
		params     *SwitchSoulByWeekParams
		today      time.Weekday
		wantGroup  string
		wantTeam   string
		wantSource string
	}{
		{
			name:       "当天有配置",
			params:     weekly,
			today:      time.Tuesday,
			wantGroup:  "御魂",
			wantTeam:   "魂十",
			wantSource: "分组来自周二配置，队伍来自周二配置",
		},
		{
			name:       "当天没有配置时用默认配置",
			params:     withDefault,
			today:      time.Sunday,
			wantGroup:  "御魂",
			wantTeam:   "魂王",
			wantSource: "分组来自默认配置，队伍来自默认配置",
		},
		{
			name:       "没有默认配置时回退周一",
			params:     weekly,
			today:      time.Sunday,
			wantGroup:  "御魂",
			wantTeam:   "魂土",
			wantSource: "分组来自周一配置，队伍来自周一配置",
		},
		{
			name:       "周一没有时按周二往后找",
			params:     &SwitchSoulByWeekParams{Tuesday: &SoulPreset{GroupName: "御魂", TeamName: "魂十"}},
			today:      time.Friday,
			wantGroup:  "御魂",
			wantTeam:   "魂十",
			wantSource: "分组来自周二配置，队伍来自周二配置",
		},
		{
			name:       "当天只有分组时队伍回退",
			params:     &SwitchSoulByWeekParams{Wednesday: &SoulPreset{GroupName: "活动分组"}, Default: &SoulPreset{TeamName: "魂王"}},
			today:      time.Wednesday,
			wantGroup:  "活动分组",
			wantTeam:   "魂王",
			wantSource: "分组来自周三配置，队伍来自默认配置",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, source, ok := tt.params.resolve(tt.today)
			if !ok {
				t.Fatalf("resolve() 失败，期望 %s/%s", tt.wantGroup, tt.wantTeam)
			}
			if got.GroupName != tt.wantGroup || got.TeamName != tt.wantTeam {
				t.Fatalf("resolve() = %s/%s，期望 %s/%s", got.GroupName, got.TeamName, tt.wantGroup, tt.wantTeam)
			}
			if source != tt.wantSource {
				t.Fatalf("resolve() 来源 = %s，期望 %s", source, tt.wantSource)
			}
		})
	}
}

func TestResolveWithoutAnyPreset(t *testing.T) {
	var params SwitchSoulByWeekParams
	if _, _, ok := params.resolve(time.Friday); ok {
		t.Fatal("resolve() 在没有任何配置时应失败")
	}
}

func TestParseParams(t *testing.T) {
	tests := []struct {
		name string
		raw  string
		want *SoulPreset
		err  bool
	}{
		{
			name: "合法参数",
			raw:  `{"monday":{"group_name":"御魂","team_name":"魂土"}}`,
			want: &SoulPreset{GroupName: "御魂", TeamName: "魂土"},
		},
		{
			name: "空参数",
			raw:  ``,
		},
		{
			name: "未知键报错",
			raw:  `{"tuesday":{"group_name":"御魂","team_name":"魂十"},"周五":{"group_name":"御魂","team_name":"魂王"}}`,
			err:  true,
		},
		{
			name: "未知字段报错",
			raw:  `{"monday":{"group_name":"御魂","team_name":"魂土","位置":"御魂"}}`,
			err:  true,
		},
		{
			name: "非法 JSON 报错",
			raw:  `[]`,
			err:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			params, err := parseParams(tt.raw)
			if tt.err {
				if err == nil {
					t.Fatalf("parseParams(%s) 期望报错", tt.raw)
				}
				return
			}
			if err != nil {
				t.Fatalf("parseParams(%s) 报错: %v", tt.raw, err)
			}
			if tt.want == nil {
				if params.Monday != nil {
					t.Fatalf("parseParams(%s) 应没有配置", tt.raw)
				}
				return
			}
			if *params.Monday != *tt.want {
				t.Fatalf("parseParams(%s) Monday = %+v", tt.raw, params.Monday)
			}
		})
	}
}
