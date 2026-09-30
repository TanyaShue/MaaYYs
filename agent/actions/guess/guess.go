package guess

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"image"
	"io"
	"math/rand"
	"net/http"
	"strings"
	"time"

	"maa-yys-agent/ocrtext"

	"github.com/MaaXYZ/maa-framework-go/v4"
	mqtt "github.com/eclipse/paho.mqtt.golang"
)

const (
	// 识别节点
	recognitionLeftCount  = "识别左侧人数"
	recognitionRightCount = "识别右侧人数"

	// 押注任务
	taskBetLeft  = "竞猜7_左边"
	taskBetRight = "竞猜10_右边"

	// 订阅消息：example/mqtt_publish.py 默认发布到这里的测试服务器
	mqttBroker = "broker-cn.emqx.io"
	mqttPort   = 1883
	mqttTopic  = "test/maayys"
	mqttQoS    = 1

	// mqttTimeout 是从连接、订阅到拿到消息的总超时。超时就当作没取到，
	// 直接走兜底策略，不能因为 MQTT 卡住把整条流水线拖死。
	mqttTimeout = 5 * time.Second

	// 网站预测：https://yysrank.com/dyjc.html 的"对弈竞猜实时风向"。
	//
	// 页面把博主发布的预测按红蓝两方统计，接口返回每条预测的方向
	// predict_winner（red 红方=左、blue 蓝方=右）与发布时间 posted_at。
	predictAPIURL = "https://yysrank.com/api/dyjc/get"

	// predictTimeout 是取网站预测的总超时。超时同样当作没取到，走兜底策略，
	// 不能因为站点慢把整条流水线拖死。
	predictTimeout = 8 * time.Second

	// predictMaxBody 限制最多读取多少响应体，防止异常响应把内存吃满。
	predictMaxBody = 1 << 20

	// predictUserAgent 用浏览器 UA，避免被站点当成脚本直接拒掉。
	predictUserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

// 押注策略
const (
	strategyMajority = "majority" // 跟着人多的选（默认策略，也是兜底策略）
	strategyRandom   = "random"   // 随机选左或右
	strategyAuthor   = "author"   // 跟随订阅作者选
	strategyPredict  = "predict"  // 跟随网站预测选（红方=左、蓝方=右，押票多的一边）
)

// 网站预测的方向取值，红方在左、蓝方在右
const (
	sideRed  = "red"  // 红方 = 左边
	sideBlue = "blue" // 蓝方 = 右边
)

// 订阅消息 values 里每个作者的取值约定
const (
	valueUnpublished = 0 // 还没发布选择
	valueLeft        = 1 // 左
	valueRight       = 2 // 右
)

// timeLayouts 是订阅消息里 valid_from / valid_until 允许的时间格式，
// 不带时区的写法按 UTC 处理。
var timeLayouts = []string{time.RFC3339, "2006-01-02T15:04:05"}

// Params 是竞猜自定义动作的 custom_action_param，一共三个参数：
//
//	{"strategy": "author", "author": "aaa"}
//	{"strategy": "predict", "url": "https://yysrank.com/api/dyjc/get"}
//
// strategy 为策略：majority 跟着人多的选、random 随机选左或右、
// author 跟随订阅作者选、predict 跟随网站预测选；也接受对应的中文写法。
// author 为跟随订阅的作者，只在 strategy 为 author 时使用。
// url 为网站预测的接口地址，只在 strategy 为 predict 时使用，留空用默认地址。
type Params struct {
	Strategy string `json:"strategy"`
	Author   string `json:"author"`
	URL      string `json:"url"`
}

// SubscribeMessage 是 example/mqtt_publish.py 发布到测试服务器上的消息格式：
//
//	{
//	  "valid_from": "2026-09-30T16:00:00Z",
//	  "valid_until": "2026-09-30T18:00:00Z",
//	  "published_at": "2026-09-30T15:58:23Z",
//	  "values": {"aaa": 1, "bbb": 2, "ccc": 0}
//	}
type SubscribeMessage struct {
	ValidFrom   string         `json:"valid_from"`
	ValidUntil  string         `json:"valid_until"`
	PublishedAt string         `json:"published_at"`
	Values      map[string]int `json:"values"`
}

// PredictResponse 是 https://yysrank.com/api/dyjc/get 的返回格式：
//
//	{
//	  "success": true,
//	  "data": [
//	    {"name": "七面相", "match": "9月30日，14:00场",
//	     "predict_winner": "red", "posted_at": "2026-09-30T15:36:40+08:00"}
//	  ]
//	}
//
// data 里既有本轮预测也有往期预测，谁算本轮由发布时间决定，见 countPredictVotes。
type PredictResponse struct {
	Success bool            `json:"success"`
	Data    []PredictRecord `json:"data"`
}

// PredictRecord 是网站预测里的一条记录，只取判断方向需要的字段，
// 其余字段（url、post 等）用不上就不解析。
type PredictRecord struct {
	Name          string `json:"name"`
	Match         string `json:"match"`
	PredictWinner string `json:"predict_winner"` // red 红方=左、blue 蓝方=右，其他值视为没给方向
	PostedAt      string `json:"posted_at"`      // 发布时间，带时区的 RFC3339
}

type Guess struct{}

// Run 执行竞猜
func (a *Guess) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：竞猜")

	params, err := parseParams(arg.CustomActionParam)
	if err != nil {
		fmt.Printf("%v\n", err)
		return false
	}
	fmt.Printf("竞猜策略: %s\n", describeStrategy(params))

	task, winner := decide(ctx, params)
	if task == "" {
		fmt.Println("未能决定押注方向")
		return false
	}

	if _, err := ctx.RunTask(task, nil); err != nil {
		fmt.Printf("执行任务失败: %s, 错误: %v\n", task, err)
		return false
	}

	fmt.Println("竞猜结束")
	fmt.Printf("选择了%s\n", winner)
	return true
}

// decide 按策略决定押注任务与方向。跟随订阅作者或跟随网站预测时，只要有一环不成立
// （连不上、消息过期、作者没发布、站点没数据），就回退到兜底策略：跟着人多的选。
func decide(ctx *maa.Context, params Params) (task, winner string) {
	switch params.Strategy {
	case strategyRandom:
		task, winner = pickRandom()
		fmt.Printf("按随机策略选择: %s\n", winner)
		return task, winner

	case strategyAuthor:
		if task, winner, ok := pickByAuthor(params.Author); ok {
			return task, winner
		}
		fmt.Println("跟随订阅作者没有拿到有效选择, 回退到兜底策略: 跟着人多的选")

	case strategyPredict:
		if task, winner, ok := pickByPredict(params.URL); ok {
			return task, winner
		}
		fmt.Println("跟随网站预测没有拿到有效结果, 回退到兜底策略: 跟着人多的选")
	}

	return pickByMajority(ctx)
}

// pickByMajority 识别两侧人数，押人数多的一边；这也是兜底策略。
func pickByMajority(ctx *maa.Context) (task, winner string) {
	controller := ctx.GetTasker().GetController()
	if controller == nil {
		fmt.Println("获取控制器失败")
		return "", ""
	}

	// 先截图
	controller.PostScreencap().Wait()
	img, err := controller.CacheImage()
	if err != nil {
		fmt.Printf("获取截图失败: %v\n", err)
		return "", ""
	}

	// 识别两侧人数：人数取自识别结果的 OCR 文本，取不到才算识别失败
	leftCount, leftText, leftOK := recognizeCount(ctx, img, recognitionLeftCount)
	rightCount, rightText, rightOK := recognizeCount(ctx, img, recognitionRightCount)

	fmt.Printf("识别左侧人数 %s\n", describeCount(leftCount, leftText, leftOK))
	fmt.Printf("识别右侧人数 %s\n", describeCount(rightCount, rightText, rightOK))

	if !leftOK || !rightOK {
		fmt.Println("警告: 人数识别失败, 无法比较, 随机选择一边竞猜")
	}
	return pickBet(leftCount, leftOK, rightCount, rightOK)
}

// pickByAuthor 取订阅主题上的最后一条消息，按作者在 values 里的取值决定方向。
// 取不到有效选择时返回 ok=false，由调用方走兜底策略。
func pickByAuthor(author string) (task, winner string, ok bool) {
	if author == "" {
		fmt.Println("策略为跟随订阅作者, 但没有填写作者名")
		return "", "", false
	}

	payload, err := lastMessageFetcher(mqttTimeout)
	if err != nil {
		fmt.Printf("获取订阅消息失败: %v\n", err)
		return "", "", false
	}

	msg, err := parseSubscribeMessage(payload)
	if err != nil {
		fmt.Printf("解析订阅消息失败: %v\n", err)
		return "", "", false
	}

	now := time.Now()
	inWindow, err := msg.withinWindow(now)
	if err != nil {
		fmt.Printf("订阅消息的有效期无法判断: %v\n", err)
		return "", "", false
	}
	if !inWindow {
		fmt.Printf("当前时间 %s 不在订阅消息的有效期 %s ~ %s 内, 该消息视为过期\n",
			now.Format(time.RFC3339), msg.ValidFrom, msg.ValidUntil)
		return "", "", false
	}

	value, exists := msg.Values[author]
	if !exists {
		fmt.Printf("订阅消息里没有作者 %q, 走兜底策略\n", author)
		return "", "", false
	}

	task, winner, ok = pickByValue(value)
	if !ok {
		fmt.Printf("作者 %q 的取值 %d 不是有效选择 (%d=未发布, %d=左, %d=右), 走兜底策略\n",
			author, value, valueUnpublished, valueLeft, valueRight)
		return "", "", false
	}

	fmt.Printf("订阅作者 %q 的选择是 %s\n", author, winner)
	return task, winner, true
}

// pickByValue 把订阅消息里的取值翻译成押注任务与方向。
func pickByValue(value int) (task, winner string, ok bool) {
	switch value {
	case valueLeft:
		return taskBetLeft, "左边", true
	case valueRight:
		return taskBetRight, "右边", true
	}
	return "", "", false
}

// pickByPredict 取网站（对弈竞猜实时风向）的博主预测统计，押票多的一方：
// 红方在左、蓝方在右。取不到有效预测时返回 ok=false，由调用方走兜底策略。
func pickByPredict(rawURL string) (task, winner string, ok bool) {
	return pickByPredictAt(rawURL, time.Now())
}

// pickByPredictAt 是 pickByPredict 的实现，now 单独传进来方便测试。
func pickByPredictAt(rawURL string, now time.Time) (task, winner string, ok bool) {
	rawURL = strings.TrimSpace(rawURL)
	if rawURL == "" {
		rawURL = predictAPIURL
	}

	payload, err := predictFetcher(rawURL)
	if err != nil {
		fmt.Printf("获取网站预测失败: %v\n", err)
		return "", "", false
	}

	parsed, err := parsePredictPayload(payload)
	if err != nil {
		fmt.Printf("解析网站预测失败: %v\n", err)
		return "", "", false
	}

	// 和网页一样，只统计截断时间之后发布的预测，往期记录不参与。
	cutoff := predictCutoff(now)
	red, blue, skipped := countPredictVotes(parsed.Data, cutoff)
	redPercent, bluePercent := predictShare(red, blue)

	fmt.Printf("网站预测: 当前 %s, 统计 %s 之后发布的 %d 条记录, 红方(左) %d 票 %d%% / 蓝方(右) %d 票 %d%%\n",
		now.Format("15:04"), cutoff.Format("15:04"), len(parsed.Data),
		red, redPercent, blue, bluePercent)
	if skipped > 0 {
		fmt.Printf("网站预测里有 %d 条记录的发布时间读不出来, 已忽略\n", skipped)
	}

	if red == 0 && blue == 0 {
		fmt.Printf("网站预测在 %s 之后没有任何明确方向\n", cutoff.Format("15:04"))
		return "", "", false
	}

	task, winner = pickByPredictVotes(red, blue)
	fmt.Printf("网站预测选择: %s\n", winner)
	return task, winner, true
}

// predictCutoff 复刻网页的统计口径：取当前时间之前最近的一个偶数整点。
// 例如 13:45 对应 12:00，14:10 对应 14:00。网页用的是浏览器本地时间，
// 这里同样按运行机器的本地时间算。
func predictCutoff(now time.Time) time.Time {
	hour := now.Hour()
	if hour%2 != 0 {
		hour--
	}
	return time.Date(now.Year(), now.Month(), now.Day(), hour, 0, 0, 0, now.Location())
}

// countPredictVotes 数一遍红蓝两方的票数：只有发布时间晚于 cutoff 的记录才算本轮预测。
// 时间读不出来或者方向不是 red/blue 的记录一律不计票（发布时间读不出来的记进 skipped，
// 和网页上 Invalid Date 比不出大小、被排除在外的结果一致）。
func countPredictVotes(records []PredictRecord, cutoff time.Time) (red, blue, skipped int) {
	for _, record := range records {
		postedAt, err := time.Parse(time.RFC3339, strings.TrimSpace(record.PostedAt))
		if err != nil {
			skipped++
			continue
		}
		if !postedAt.After(cutoff) {
			continue
		}

		switch strings.ToLower(strings.TrimSpace(record.PredictWinner)) {
		case sideRed:
			red++
		case sideBlue:
			blue++
		}
	}
	return red, blue, skipped
}

// predictShare 算红蓝两方的占比（百分比），按网页的算法四舍五入到整数。
func predictShare(red, blue int) (redPercent, bluePercent int) {
	total := red + blue
	if total == 0 {
		return 50, 50
	}
	return (red*100 + total/2) / total, (blue*100 + total/2) / total
}

// pickByPredictVotes 按红蓝票数决定押注任务与方向：红方在左、蓝方在右。
// 票数一样时没有倾向，和人数策略保持一致，押左边。
func pickByPredictVotes(red, blue int) (task, winner string) {
	if blue > red {
		return taskBetRight, "右边"
	}
	return taskBetLeft, "左边"
}

// predictFetcher 负责请求网站预测接口，做成变量方便测试替换。
var predictFetcher = fetchPredict

// fetchPredict 请求网站预测接口并返回响应体。超时、状态码异常、响应过大都当失败，
// 由调用方走兜底策略。这里不保持任何连接，请求完就断。
func fetchPredict(rawURL string) ([]byte, error) {
	req, err := http.NewRequest(http.MethodGet, rawURL, nil)
	if err != nil {
		return nil, fmt.Errorf("请求地址 %q 不合法: %w", rawURL, err)
	}
	req.Header.Set("User-Agent", predictUserAgent)
	req.Header.Set("Accept", "application/json, text/plain, */*")

	client := &http.Client{Timeout: predictTimeout}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("%s 内请求 %s 失败: %w", predictTimeout, rawURL, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("请求 %s 返回 HTTP %d", rawURL, resp.StatusCode)
	}

	body, err := io.ReadAll(io.LimitReader(resp.Body, predictMaxBody))
	if err != nil {
		return nil, fmt.Errorf("读取 %s 的响应失败: %w", rawURL, err)
	}
	return body, nil
}

// parsePredictPayload 解析网站预测接口返回的 payload。
func parsePredictPayload(payload []byte) (PredictResponse, error) {
	var parsed PredictResponse
	if len(bytes.TrimSpace(payload)) == 0 {
		return parsed, errors.New("响应内容为空")
	}
	if err := json.Unmarshal(payload, &parsed); err != nil {
		return parsed, fmt.Errorf("不是合法的 JSON: %w", err)
	}
	if !parsed.Success {
		return parsed, errors.New("接口返回 success=false")
	}
	return parsed, nil
}

// withinWindow 判断 now 是否落在 valid_from ~ valid_until 之间（两端都算）。
// 某一侧留空表示那一侧不限；两侧都空说明这条消息没有有效期，按无效处理。
func (m SubscribeMessage) withinWindow(now time.Time) (bool, error) {
	from, err := parseMessageTime(m.ValidFrom)
	if err != nil {
		return false, fmt.Errorf("valid_from: %w", err)
	}
	until, err := parseMessageTime(m.ValidUntil)
	if err != nil {
		return false, fmt.Errorf("valid_until: %w", err)
	}
	if from.IsZero() && until.IsZero() {
		return false, errors.New("valid_from 与 valid_until 都是空的")
	}

	if !from.IsZero() && now.Before(from) {
		return false, nil
	}
	if !until.IsZero() && now.After(until) {
		return false, nil
	}
	return true, nil
}

// parseMessageTime 解析订阅消息里的时间戳，空字符串表示该侧不限制时间。
func parseMessageTime(value string) (time.Time, error) {
	value = strings.TrimSpace(value)
	if value == "" {
		return time.Time{}, nil
	}
	for _, layout := range timeLayouts {
		if parsed, err := time.Parse(layout, value); err == nil {
			return parsed, nil
		}
	}
	return time.Time{}, fmt.Errorf("无法解析时间 %q", value)
}

// parseSubscribeMessage 解析订阅到的 payload。
func parseSubscribeMessage(payload []byte) (SubscribeMessage, error) {
	var msg SubscribeMessage
	if len(bytes.TrimSpace(payload)) == 0 {
		return msg, errors.New("消息内容为空")
	}
	if err := json.Unmarshal(payload, &msg); err != nil {
		return msg, fmt.Errorf("不是合法的 JSON: %w", err)
	}
	return msg, nil
}

// lastMessageFetcher 负责取订阅主题上的最后一条消息，做成变量方便测试替换。
var lastMessageFetcher = fetchLastMessage

// fetchLastMessage 连上测试服务器，订阅主题，拿到最后一条（保留）消息后立刻断开：
// 不保持长连接，也不等第二条消息。连接、订阅、等消息共用一份超时预算。
func fetchLastMessage(timeout time.Duration) ([]byte, error) {
	addr := fmt.Sprintf("tcp://%s:%d", mqttBroker, mqttPort)
	deadline := time.Now().Add(timeout)

	// remaining 返回距离总超时还剩多少时间，用完了就返回 0（等待会立刻超时）。
	remaining := func() time.Duration {
		left := time.Until(deadline)
		if left < 0 {
			return 0
		}
		return left
	}

	opts := mqtt.NewClientOptions().
		AddBroker(addr).
		SetClientID(fmt.Sprintf("maayys-guess-%08x", rand.Uint32())).
		SetCleanSession(true).
		SetAutoReconnect(false). // 掉线不重连
		SetConnectRetry(false).  // 连不上立刻报错，不在后台一直重试
		SetConnectTimeout(timeout)

	client := mqtt.NewClient(opts)
	// 无论后面成功还是失败，退出前都把连接关掉，不留长连接。
	defer client.Disconnect(0)

	if err := mqtt.WaitTokenTimeout(client.Connect(), remaining()); err != nil {
		if errors.Is(err, mqtt.TimedOut) {
			return nil, fmt.Errorf("%s 内没连上 %s", timeout, addr)
		}
		return nil, fmt.Errorf("连接 %s 失败: %w", addr, err)
	}

	// 订阅带 retain 的主题，broker 会立刻把最后一条保留消息推过来，收到一条就够。
	messages := make(chan []byte, 1)
	subscribeToken := client.Subscribe(mqttTopic, mqttQoS, func(_ mqtt.Client, msg mqtt.Message) {
		payload := append([]byte(nil), msg.Payload()...)
		select {
		case messages <- payload:
		default:
		}
	})
	if err := mqtt.WaitTokenTimeout(subscribeToken, remaining()); err != nil {
		if errors.Is(err, mqtt.TimedOut) {
			return nil, fmt.Errorf("%s 内没订阅上 %s", timeout, mqttTopic)
		}
		return nil, fmt.Errorf("订阅 %s 失败: %w", mqttTopic, err)
	}

	select {
	case payload := <-messages:
		return payload, nil
	case <-time.After(remaining()):
		return nil, fmt.Errorf("%s 内没读到 %s 上的保留消息", timeout, mqttTopic)
	}
}

// parseParams 解析 custom_action_param，没传参数时按兜底策略（跟着人多的选）执行。
func parseParams(raw string) (Params, error) {
	params := Params{Strategy: strategyMajority}
	if strings.TrimSpace(raw) == "" {
		return params, nil
	}
	if err := json.Unmarshal([]byte(raw), &params); err != nil {
		return params, fmt.Errorf("参数JSON解析失败: %w", err)
	}

	strategy, err := normalizeStrategy(params.Strategy)
	if err != nil {
		return params, err
	}
	params.Strategy = strategy
	params.Author = strings.TrimSpace(params.Author)
	params.URL = strings.TrimSpace(params.URL)
	return params, nil
}

// normalizeStrategy 把参数里的策略写法统一成内部取值，中英文都认。
func normalizeStrategy(raw string) (string, error) {
	switch strings.ToLower(strings.TrimSpace(raw)) {
	case "", strategyMajority, "count", "人多", "人多的", "跟着人多的", "跟人多的", "跟随人多的":
		return strategyMajority, nil
	case strategyRandom, "rand", "随机", "随机选择", "随机选一边":
		return strategyRandom, nil
	case strategyAuthor, "subscribe", "subscribe_author", "订阅", "作者", "订阅作者", "跟随订阅作者":
		return strategyAuthor, nil
	case strategyPredict, "web", "yysrank", "dyjc", "预测", "网站", "网站预测", "跟随网站预测", "看预测", "跟预测", "风向", "实时风向":
		return strategyPredict, nil
	}
	return "", fmt.Errorf("未知的竞猜策略 %q (可选: majority=跟着人多的选, random=随机选, author=跟随订阅作者, predict=跟随网站预测)", raw)
}

// describeStrategy 生成日志里的策略描述。
func describeStrategy(params Params) string {
	switch params.Strategy {
	case strategyRandom:
		return "随机选择"
	case strategyAuthor:
		return fmt.Sprintf("跟随订阅作者(%s)", params.Author)
	case strategyPredict:
		if params.URL != "" {
			return fmt.Sprintf("跟随网站预测(%s)", params.URL)
		}
		return "跟随网站预测"
	}
	return "跟着人多的选"
}

// pickRandom 随机押一边。
func pickRandom() (task, winner string) {
	if rand.Intn(2) == 1 {
		return taskBetRight, "右边"
	}
	return taskBetLeft, "左边"
}

// pickBet 根据两侧人数决定押注任务与方向。
// 人数相同时押左边；有一侧识别失败时无法比较，随机押一边，避免因识别波动中断流水线。
func pickBet(leftCount int, leftOK bool, rightCount int, rightOK bool) (task, winner string) {
	if !leftOK || !rightOK {
		return pickRandom()
	}
	if rightCount > leftCount {
		return taskBetRight, "右边"
	}
	return taskBetLeft, "左边"
}

// recognizeCount 运行指定识别节点并解析出人数，返回人数、原始 OCR 文本和是否解析成功。
func recognizeCount(ctx *maa.Context, img image.Image, node string) (int, string, bool) {
	detail, err := ctx.RunRecognition(node, img, nil)
	if err != nil {
		fmt.Printf("运行识别节点 %s 失败: %v\n", node, err)
		return 0, "", false
	}
	if detail == nil {
		fmt.Printf("运行识别节点 %s 未返回识别详情\n", node)
		return 0, "", false
	}

	texts := ocrtext.Texts(detail)
	if count, text, ok := ocrtext.Number(texts); ok {
		return count, text, true
	}

	fmt.Printf("识别节点 %s 未解析出人数 (hit=%v, OCR文本=%v)\n", node, detail.Hit, texts)
	return 0, "", false
}

// describeCount 生成日志中的人数描述，解析失败时明确标出失败。
func describeCount(count int, text string, ok bool) string {
	if !ok {
		return "失败"
	}
	return ocrtext.Describe(count, text)
}
