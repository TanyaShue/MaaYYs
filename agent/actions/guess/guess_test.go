package guess

import (
	"encoding/json"
	"errors"
	"testing"
	"time"
)

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

// TestPickRandom 随机策略必须只产生左右两边，且两边都可能出现。
func TestPickRandom(t *testing.T) {
	seen := map[string]bool{}
	for range 200 {
		task, winner := pickRandom()
		if (task == taskBetLeft && winner != "左边") || (task == taskBetRight && winner != "右边") {
			t.Fatalf("pickRandom() 返回了不匹配的组合: (%q, %q)", task, winner)
		}
		seen[task] = true
	}
	if len(seen) != 2 {
		t.Errorf("随机策略应该两边都能选到, 实际只出现了 %v", seen)
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

func TestNormalizeStrategy(t *testing.T) {
	tests := []struct {
		raw  string
		want string
	}{
		{raw: "", want: strategyMajority},
		{raw: "majority", want: strategyMajority},
		{raw: "  MAJORITY ", want: strategyMajority},
		{raw: "跟着人多的", want: strategyMajority},
		{raw: "跟随人多的", want: strategyMajority},
		{raw: "random", want: strategyRandom},
		{raw: "随机选择", want: strategyRandom},
		{raw: "author", want: strategyAuthor},
		{raw: "subscribe", want: strategyAuthor},
		{raw: "跟随订阅作者", want: strategyAuthor},
		{raw: "predict", want: strategyPredict},
		{raw: "yysrank", want: strategyPredict},
		{raw: "网站预测", want: strategyPredict},
		{raw: "跟随网站预测", want: strategyPredict},
		{raw: "风向", want: strategyPredict},
	}

	for _, tt := range tests {
		t.Run(tt.raw, func(t *testing.T) {
			got, err := normalizeStrategy(tt.raw)
			if err != nil {
				t.Fatalf("normalizeStrategy(%q) 返回错误: %v", tt.raw, err)
			}
			if got != tt.want {
				t.Errorf("normalizeStrategy(%q) = %q, want %q", tt.raw, got, tt.want)
			}
		})
	}

	if _, err := normalizeStrategy("随便押"); err == nil {
		t.Error("未知策略应该报错")
	}
}

func TestParseParams(t *testing.T) {
	// 没传参数时用兜底策略
	params, err := parseParams("")
	if err != nil {
		t.Fatalf("parseParams(空) 返回错误: %v", err)
	}
	if params.Strategy != strategyMajority {
		t.Errorf("parseParams(空).Strategy = %q, want %q", params.Strategy, strategyMajority)
	}

	params, err = parseParams(`{"strategy": "author", "author": " aaa "}`)
	if err != nil {
		t.Fatalf("parseParams(author) 返回错误: %v", err)
	}
	if params.Strategy != strategyAuthor || params.Author != "aaa" {
		t.Errorf("parseParams(author) = %+v, want strategy=author, author=aaa", params)
	}

	params, err = parseParams(`{"strategy": "跟随订阅作者"}`)
	if err != nil {
		t.Fatalf("parseParams(中文策略) 返回错误: %v", err)
	}
	if params.Strategy != strategyAuthor {
		t.Errorf("parseParams(中文策略).Strategy = %q", params.Strategy)
	}

	params, err = parseParams(`{"strategy": "predict", "url": " https://example.com/api "}`)
	if err != nil {
		t.Fatalf("parseParams(predict) 返回错误: %v", err)
	}
	if params.Strategy != strategyPredict || params.URL != "https://example.com/api" {
		t.Errorf("parseParams(predict) = %+v, want strategy=predict, url=https://example.com/api", params)
	}

	// 不填 url 时留空，运行时用默认地址
	params, err = parseParams(`{"strategy": "网站预测"}`)
	if err != nil {
		t.Fatalf("parseParams(网站预测) 返回错误: %v", err)
	}
	if params.Strategy != strategyPredict || params.URL != "" {
		t.Errorf("parseParams(网站预测) = %+v, want strategy=predict, url 为空", params)
	}

	if _, err := parseParams(`{"strategy": "author"`); err == nil {
		t.Error("非法 JSON 应该报错")
	}
	if _, err := parseParams(`{"strategy": "猜拳"}`); err == nil {
		t.Error("未知策略应该报错")
	}
}

func TestPickByValue(t *testing.T) {
	tests := []struct {
		value      int
		wantTask   string
		wantWinner string
		wantOK     bool
	}{
		{value: valueLeft, wantTask: taskBetLeft, wantWinner: "左边", wantOK: true},
		{value: valueRight, wantTask: taskBetRight, wantWinner: "右边", wantOK: true},
		{value: valueUnpublished, wantOK: false},
		{value: 9, wantOK: false},
	}

	for _, tt := range tests {
		task, winner, ok := pickByValue(tt.value)
		if ok != tt.wantOK || task != tt.wantTask || winner != tt.wantWinner {
			t.Errorf("pickByValue(%d) = (%q, %q, %v), want (%q, %q, %v)",
				tt.value, task, winner, ok, tt.wantTask, tt.wantWinner, tt.wantOK)
		}
	}
}

func TestWithinWindow(t *testing.T) {
	now := time.Date(2026, 9, 30, 17, 0, 0, 0, time.UTC)

	tests := []struct {
		name    string
		msg     SubscribeMessage
		want    bool
		wantErr bool
	}{
		{
			name: "落在有效期中间",
			msg:  SubscribeMessage{ValidFrom: "2026-09-30T16:00:00Z", ValidUntil: "2026-09-30T18:00:00Z"},
			want: true,
		},
		{
			name: "刚好是起始时间",
			msg:  SubscribeMessage{ValidFrom: "2026-09-30T17:00:00Z", ValidUntil: "2026-09-30T18:00:00Z"},
			want: true,
		},
		{
			name: "刚好是结束时间",
			msg:  SubscribeMessage{ValidFrom: "2026-09-30T16:00:00Z", ValidUntil: "2026-09-30T17:00:00Z"},
			want: true,
		},
		{
			name: "还没到起始时间",
			msg:  SubscribeMessage{ValidFrom: "2026-09-30T18:00:00Z", ValidUntil: "2026-09-30T19:00:00Z"},
			want: false,
		},
		{
			name: "已经过了结束时间",
			msg:  SubscribeMessage{ValidFrom: "2026-09-30T14:00:00Z", ValidUntil: "2026-09-30T15:00:00Z"},
			want: false,
		},
		{
			name: "带时区偏移的时间",
			msg:  SubscribeMessage{ValidFrom: "2026-10-01T00:00:00+08:00", ValidUntil: "2026-10-01T02:00:00+08:00"},
			want: true,
		},
		{
			name: "没有时区的时间按 UTC 处理",
			msg:  SubscribeMessage{ValidFrom: "2026-09-30T16:00:00", ValidUntil: "2026-09-30T18:00:00"},
			want: true,
		},
		{
			name: "只给起始时间",
			msg:  SubscribeMessage{ValidFrom: "2026-09-30T16:00:00Z"},
			want: true,
		},
		{
			name: "只给结束时间",
			msg:  SubscribeMessage{ValidUntil: "2026-09-30T18:00:00Z"},
			want: true,
		},
		{
			name:    "两个时间都为空",
			msg:     SubscribeMessage{},
			wantErr: true,
		},
		{
			name:    "时间格式不认识",
			msg:     SubscribeMessage{ValidFrom: "昨晚八点", ValidUntil: "2026-09-30T18:00:00Z"},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := tt.msg.withinWindow(now)
			if tt.wantErr {
				if err == nil {
					t.Fatalf("withinWindow() 应该报错, 实际返回 %v", got)
				}
				return
			}
			if err != nil {
				t.Fatalf("withinWindow() 返回错误: %v", err)
			}
			if got != tt.want {
				t.Errorf("withinWindow() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestParseSubscribeMessage(t *testing.T) {
	payload := []byte(`{"valid_from":"2026-09-30T16:00:00Z","valid_until":"2026-09-30T18:00:00Z",` +
		`"published_at":"2026-09-30T15:58:23Z","values":{"aaa":1,"bbb":2,"ccc":0}}`)

	msg, err := parseSubscribeMessage(payload)
	if err != nil {
		t.Fatalf("parseSubscribeMessage() 返回错误: %v", err)
	}
	if msg.Values["aaa"] != valueLeft || msg.Values["bbb"] != valueRight || msg.Values["ccc"] != valueUnpublished {
		t.Errorf("values 解析结果不对: %v", msg.Values)
	}

	if _, err := parseSubscribeMessage(nil); err == nil {
		t.Error("空 payload（保留消息被清掉）应该报错")
	}
	if _, err := parseSubscribeMessage([]byte("hello")); err == nil {
		t.Error("非 JSON payload 应该报错")
	}
}

// stubLastMessage 替换取消息的实现，测试里不连真的 broker。
func stubLastMessage(t *testing.T, payload string, err error) *int {
	t.Helper()
	calls := 0
	original := lastMessageFetcher
	lastMessageFetcher = func(time.Duration) ([]byte, error) {
		calls++
		return []byte(payload), err
	}
	t.Cleanup(func() { lastMessageFetcher = original })
	return &calls
}

// buildPayload 按 example/mqtt_publish.py 的格式拼一条订阅消息。
func buildPayload(t *testing.T, from, until time.Time, values map[string]int) string {
	t.Helper()
	raw, err := json.Marshal(SubscribeMessage{
		ValidFrom:  from.Format(time.RFC3339),
		ValidUntil: until.Format(time.RFC3339),
		Values:     values,
	})
	if err != nil {
		t.Fatalf("拼测试 payload 失败: %v", err)
	}
	return string(raw)
}

func TestPickByAuthor(t *testing.T) {
	now := time.Now()
	from, until := now.Add(-time.Hour), now.Add(time.Hour)

	tests := []struct {
		name       string
		author     string
		payload    string
		fetchErr   error
		wantTask   string
		wantWinner string
		wantOK     bool
	}{
		{
			name:       "作者选了左",
			author:     "aaa",
			payload:    buildPayload(t, from, until, map[string]int{"aaa": valueLeft, "bbb": valueRight}),
			wantTask:   taskBetLeft,
			wantWinner: "左边",
			wantOK:     true,
		},
		{
			name:       "作者选了右",
			author:     "bbb",
			payload:    buildPayload(t, from, until, map[string]int{"aaa": valueLeft, "bbb": valueRight}),
			wantTask:   taskBetRight,
			wantWinner: "右边",
			wantOK:     true,
		},
		{
			name:    "作者还没发布",
			author:  "ccc",
			payload: buildPayload(t, from, until, map[string]int{"aaa": valueLeft, "ccc": valueUnpublished}),
			wantOK:  false,
		},
		{
			name:    "消息里没有这个作者",
			author:  "zzz",
			payload: buildPayload(t, from, until, map[string]int{"aaa": valueLeft}),
			wantOK:  false,
		},
		{
			name:    "当前时间不在有效期内",
			author:  "aaa",
			payload: buildPayload(t, now.Add(-2*time.Hour), now.Add(-time.Hour), map[string]int{"aaa": valueLeft}),
			wantOK:  false,
		},
		{
			name:    "还没到生效时间",
			author:  "aaa",
			payload: buildPayload(t, now.Add(time.Hour), now.Add(2*time.Hour), map[string]int{"aaa": valueLeft}),
			wantOK:  false,
		},
		{
			name:    "有效期解析不了",
			author:  "aaa",
			payload: `{"valid_from":"昨晚八点","valid_until":"2026-09-30T18:00:00Z","values":{"aaa":1}}`,
			wantOK:  false,
		},
		{
			name:     "取消息失败",
			author:   "aaa",
			fetchErr: errors.New("连不上 broker"),
			wantOK:   false,
		},
		{
			name:    "payload 不是 JSON",
			author:  "aaa",
			payload: "whatever",
			wantOK:  false,
		},
		{
			name:   "没有配置作者",
			author: "",
			// 没填作者时不该去连 broker，靠 calls 断言
			payload: buildPayload(t, from, until, map[string]int{"aaa": valueLeft}),
			wantOK:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			calls := stubLastMessage(t, tt.payload, tt.fetchErr)

			task, winner, ok := pickByAuthor(tt.author)
			if ok != tt.wantOK || task != tt.wantTask || winner != tt.wantWinner {
				t.Errorf("pickByAuthor(%q) = (%q, %q, %v), want (%q, %q, %v)",
					tt.author, task, winner, ok, tt.wantTask, tt.wantWinner, tt.wantOK)
			}
			if tt.author == "" && *calls != 0 {
				t.Errorf("作者名为空时不应该去取消息, 实际取了 %d 次", *calls)
			}
		})
	}
}

// TestPredictCutoff 网站的统计口径是"当前时间之前最近的偶数整点"。
func TestPredictCutoff(t *testing.T) {
	loc := time.FixedZone("CST", 8*3600)

	tests := []struct {
		name string
		now  time.Time
		want string
	}{
		{name: "偶数整点就是自己", now: time.Date(2026, 9, 30, 14, 0, 0, 0, loc), want: "2026-09-30 14:00"},
		{name: "偶数整点后十分钟", now: time.Date(2026, 9, 30, 14, 10, 0, 0, loc), want: "2026-09-30 14:00"},
		{name: "奇数整点回退一小时", now: time.Date(2026, 9, 30, 13, 45, 0, 0, loc), want: "2026-09-30 12:00"},
		{name: "奇数整点整点回退一小时", now: time.Date(2026, 9, 30, 15, 0, 0, 0, loc), want: "2026-09-30 14:00"},
		{name: "凌晨一点回退到零点", now: time.Date(2026, 9, 30, 1, 30, 0, 0, loc), want: "2026-09-30 00:00"},
		{name: "零点保持零点", now: time.Date(2026, 9, 30, 0, 30, 0, 0, loc), want: "2026-09-30 00:00"},
		{name: "二十三点回退到二十二点", now: time.Date(2026, 9, 30, 23, 59, 0, 0, loc), want: "2026-09-30 22:00"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := predictCutoff(tt.now)
			if got.Format("2006-01-02 15:04") != tt.want {
				t.Errorf("predictCutoff(%s) = %s, want %s",
					tt.now.Format("2006-01-02 15:04"), got.Format("2006-01-02 15:04"), tt.want)
			}
		})
	}
}

// TestCountPredictVotes 只统计截断时间之后的记录，红方蓝方分开数。
func TestCountPredictVotes(t *testing.T) {
	loc := time.FixedZone("CST", 8*3600)
	cutoff := time.Date(2026, 9, 30, 14, 0, 0, 0, loc)

	records := []PredictRecord{
		{Name: "甲", PredictWinner: "red", PostedAt: "2026-09-30T15:29:25+08:00"},  // 本轮, 红
		{Name: "乙", PredictWinner: "blue", PostedAt: "2026-09-30T15:15:53+08:00"}, // 本轮, 蓝
		{Name: "丙", PredictWinner: "blue", PostedAt: "2026-09-30T14:35:16+08:00"}, // 本轮, 蓝
		{Name: "丁", PredictWinner: "red", PostedAt: "2026-09-30T14:00:00+08:00"},  // 刚好是截断时间, 不算本轮
		{Name: "戊", PredictWinner: "red", PostedAt: "2026-09-30T10:00:55+08:00"},  // 往期
		{Name: "己", PredictWinner: "", PostedAt: "2026-09-30T15:30:00+08:00"},     // 没给方向
		{Name: "庚", PredictWinner: "none", PostedAt: "2026-09-30T15:31:00+08:00"}, // 方向不认识
		{Name: "辛", PredictWinner: "red", PostedAt: "昨晚八点"},                       // 时间读不出来
		{Name: "壬", PredictWinner: "RED", PostedAt: "2026-09-30T15:32:00+08:00"},  // 大小写不影响
	}

	red, blue, skipped := countPredictVotes(records, cutoff)
	if red != 2 || blue != 2 {
		t.Errorf("countPredictVotes() = (%d, %d), want (2, 2)", red, blue)
	}
	if skipped != 1 {
		t.Errorf("countPredictVotes() skipped = %d, want 1", skipped)
	}

	// 时间换成 UTC 写法也要能正确比较
	red, blue, skipped = countPredictVotes([]PredictRecord{
		{PredictWinner: "red", PostedAt: "2026-09-30T07:30:00Z"}, // 北京时间 15:30, 本轮
		{PredictWinner: "red", PostedAt: "2026-09-30T05:00:00Z"}, // 北京时间 13:00, 往期
	}, cutoff)
	if red != 1 || blue != 0 || skipped != 0 {
		t.Errorf("countPredictVotes(UTC 写法) = (%d, %d, %d), want (1, 0, 0)", red, blue, skipped)
	}
}

func TestPredictShare(t *testing.T) {
	tests := []struct {
		red, blue                     int
		wantRedPercent, wantBlueShare int
	}{
		{red: 3, blue: 1, wantRedPercent: 75, wantBlueShare: 25},
		{red: 1, blue: 3, wantRedPercent: 25, wantBlueShare: 75},
		{red: 2, blue: 2, wantRedPercent: 50, wantBlueShare: 50},
		{red: 0, blue: 0, wantRedPercent: 50, wantBlueShare: 50},
		{red: 7, blue: 6, wantRedPercent: 54, wantBlueShare: 46}, // 四舍五入
	}

	for _, tt := range tests {
		gotRed, gotBlue := predictShare(tt.red, tt.blue)
		if gotRed != tt.wantRedPercent || gotBlue != tt.wantBlueShare {
			t.Errorf("predictShare(%d, %d) = (%d, %d), want (%d, %d)",
				tt.red, tt.blue, gotRed, gotBlue, tt.wantRedPercent, tt.wantBlueShare)
		}
	}
}

// TestPickByPredictVotes 红方在左、蓝方在右，票数一样时按人数策略的习惯押左边。
func TestPickByPredictVotes(t *testing.T) {
	tests := []struct {
		red, blue            int
		wantTask, wantWinner string
	}{
		{red: 12, blue: 3, wantTask: taskBetLeft, wantWinner: "左边"},
		{red: 3, blue: 12, wantTask: taskBetRight, wantWinner: "右边"},
		{red: 5, blue: 5, wantTask: taskBetLeft, wantWinner: "左边"},
		{red: 0, blue: 1, wantTask: taskBetRight, wantWinner: "右边"},
		{red: 1, blue: 0, wantTask: taskBetLeft, wantWinner: "左边"},
	}

	for _, tt := range tests {
		task, winner := pickByPredictVotes(tt.red, tt.blue)
		if task != tt.wantTask || winner != tt.wantWinner {
			t.Errorf("pickByPredictVotes(%d, %d) = (%q, %q), want (%q, %q)",
				tt.red, tt.blue, task, winner, tt.wantTask, tt.wantWinner)
		}
	}
}

func TestParsePredictPayload(t *testing.T) {
	payload := []byte(`{"success":true,"data":[{"url":"https://weibo.com/1","name":"奉天城公子奉天",` +
		`"match":"9月30日，14:00场","predict_winner":"blue","post":"压蓝",` +
		`"posted_at":"2026-09-30T15:15:53+08:00"}]}`)

	parsed, err := parsePredictPayload(payload)
	if err != nil {
		t.Fatalf("parsePredictPayload() 返回错误: %v", err)
	}
	if !parsed.Success || len(parsed.Data) != 1 {
		t.Fatalf("parsePredictPayload() = %+v, want 1 条记录", parsed)
	}
	record := parsed.Data[0]
	if record.Name != "奉天城公子奉天" || record.PredictWinner != sideBlue ||
		record.PostedAt != "2026-09-30T15:15:53+08:00" {
		t.Errorf("记录解析结果不对: %+v", record)
	}

	if _, err := parsePredictPayload(nil); err == nil {
		t.Error("空 payload 应该报错")
	}
	if _, err := parsePredictPayload([]byte("hello")); err == nil {
		t.Error("非 JSON payload 应该报错")
	}
	if _, err := parsePredictPayload([]byte(`{"success":false,"data":[]}`)); err == nil {
		t.Error("success=false 应该报错")
	}
}

// stubPredict 替换请求网站预测的实现，测试里不请求真的站点，并记录请求过的地址。
func stubPredict(t *testing.T, payload string, err error) *[]string {
	t.Helper()
	var urls []string
	original := predictFetcher
	predictFetcher = func(url string) ([]byte, error) {
		urls = append(urls, url)
		return []byte(payload), err
	}
	t.Cleanup(func() { predictFetcher = original })
	return &urls
}

// buildPredictPayload 按网站接口的返回格式拼一条响应。
func buildPredictPayload(t *testing.T, records ...PredictRecord) string {
	t.Helper()
	raw, err := json.Marshal(PredictResponse{Success: true, Data: records})
	if err != nil {
		t.Fatalf("拼测试 payload 失败: %v", err)
	}
	return string(raw)
}

func TestPickByPredictAt(t *testing.T) {
	// 15:45 的截断时间是 14:00，下面按这个口径准备数据
	now := time.Date(2026, 9, 30, 15, 45, 0, 0, time.Local)
	at := func(hour, minute int) string {
		return time.Date(2026, 9, 30, hour, minute, 0, 0, time.Local).Format(time.RFC3339)
	}

	tests := []struct {
		name       string
		url        string
		payload    string
		fetchErr   error
		wantTask   string
		wantWinner string
		wantOK     bool
		wantURL    string
	}{
		{
			name:       "红的票多押左边",
			payload:    buildPredictPayload(t, PredictRecord{PredictWinner: sideRed, PostedAt: at(15, 29)}, PredictRecord{PredictWinner: sideRed, PostedAt: at(15, 20)}, PredictRecord{PredictWinner: sideBlue, PostedAt: at(15, 15)}),
			wantTask:   taskBetLeft,
			wantWinner: "左边",
			wantOK:     true,
			wantURL:    predictAPIURL,
		},
		{
			name:       "蓝的票多押右边",
			payload:    buildPredictPayload(t, PredictRecord{PredictWinner: sideBlue, PostedAt: at(15, 29)}, PredictRecord{PredictWinner: sideBlue, PostedAt: at(15, 20)}, PredictRecord{PredictWinner: sideRed, PostedAt: at(15, 15)}),
			wantTask:   taskBetRight,
			wantWinner: "右边",
			wantOK:     true,
			wantURL:    predictAPIURL,
		},
		{
			name:       "票数一样押左边",
			payload:    buildPredictPayload(t, PredictRecord{PredictWinner: sideRed, PostedAt: at(15, 29)}, PredictRecord{PredictWinner: sideBlue, PostedAt: at(15, 20)}),
			wantTask:   taskBetLeft,
			wantWinner: "左边",
			wantOK:     true,
			wantURL:    predictAPIURL,
		},
		{
			name:    "本轮还没有数据",
			payload: buildPredictPayload(t, PredictRecord{PredictWinner: sideRed, PostedAt: at(13, 50)}, PredictRecord{PredictWinner: sideBlue, PostedAt: at(10, 0)}),
			wantOK:  false,
			wantURL: predictAPIURL,
		},
		{
			name:    "一条记录都没有",
			payload: buildPredictPayload(t),
			wantOK:  false,
			wantURL: predictAPIURL,
		},
		{
			name:    "都是没给方向的记录",
			payload: buildPredictPayload(t, PredictRecord{PredictWinner: "", PostedAt: at(15, 29)}, PredictRecord{PredictWinner: "none", PostedAt: at(15, 20)}),
			wantOK:  false,
			wantURL: predictAPIURL,
		},
		{
			name:     "请求失败",
			fetchErr: errors.New("连不上站点"),
			wantOK:   false,
			wantURL:  predictAPIURL,
		},
		{
			name:    "返回的不是 JSON",
			payload: "<html>502 Bad Gateway</html>",
			wantOK:  false,
			wantURL: predictAPIURL,
		},
		{
			name:    "接口返回失败",
			payload: `{"success":false,"data":[]}`,
			wantOK:  false,
			wantURL: predictAPIURL,
		},
		{
			name:       "自定义地址时用自定义的",
			url:        " https://example.com/api/dyjc ",
			payload:    buildPredictPayload(t, PredictRecord{PredictWinner: sideBlue, PostedAt: at(15, 29)}),
			wantTask:   taskBetRight,
			wantWinner: "右边",
			wantOK:     true,
			wantURL:    "https://example.com/api/dyjc",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			urls := stubPredict(t, tt.payload, tt.fetchErr)

			task, winner, ok := pickByPredictAt(tt.url, now)
			if ok != tt.wantOK || task != tt.wantTask || winner != tt.wantWinner {
				t.Errorf("pickByPredictAt() = (%q, %q, %v), want (%q, %q, %v)",
					task, winner, ok, tt.wantTask, tt.wantWinner, tt.wantOK)
			}
			if len(*urls) != 1 || (*urls)[0] != tt.wantURL {
				t.Errorf("请求地址 = %v, want [%q]", *urls, tt.wantURL)
			}
		})
	}
}
