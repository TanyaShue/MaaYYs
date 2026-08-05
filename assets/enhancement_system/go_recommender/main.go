package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type inputAttribute struct {
	Name  string `json:"name"`
	Value string `json:"value"`
}

type inputSoul struct {
	Type       string `json:"type"`
	Position   int    `json:"position"`
	Level      int    `json:"level"`
	Attributes struct {
		Main inputAttribute   `json:"main"`
		Subs []inputAttribute `json:"subs"`
	} `json:"attributes"`
}

type route struct {
	Name      string
	Attrs     []string
	Weights   map[string]float64
	TopN      int
	Threshold float64
	Note      string
}

type rawRoute struct {
	Name      string    `json:"路线名称"`
	Attrs     []string  `json:"有效属性"`
	Weights   []float64 `json:"有效属性权重"`
	TopN      int       `json:"Top_N"`
	Threshold float64   `json:"属性阈值"`
	Note      string    `json:"说明"`
}

type rawPosition struct {
	Main   string     `json:"主属性"`
	Routes []rawRoute `json:"推荐路线"`
}

type rawConfig struct {
	Name      string                     `json:"御魂名称"`
	Positions map[string]json.RawMessage `json:"位置配置"`
}

type poolAttribute struct {
	Name  string `json:"类型"`
	Value string `json:"数值"`
}

type poolSoul struct {
	Position int             `json:"位置"`
	Type     string          `json:"类型"`
	Main     poolAttribute   `json:"主属性"`
	Subs     []poolAttribute `json:"副属性"`
}

type poolFile struct {
	Equips []poolSoul `json:"equips"`
}

type attrState struct {
	Name        string
	FutureRolls int
}

type probabilityState struct {
	Attrs []attrState
	Prob  float64
}

type hitDistribution struct {
	Name  string
	Probs map[int]float64
}

type routeResult struct {
	Route          route
	CurrentScore   float64
	PoolThreshold  float64
	PoolCount      int
	SuccessProb    float64
	Expected       float64
	Minimum        float64
	Maximum        float64
	P10            float64
	P50            float64
	P90            float64
	StageThreshold float64
	Hits           []hitDistribution
	ScoreTargets   []targetProbability
}

type targetProbability struct {
	Score float64
	Prob  float64
}

var attrMax = map[string]float64{
	"攻击": 27.0, "生命": 114.0, "防御": 5.0,
	"防御加成": 0.03, "暴击": 0.03, "攻击加成": 0.03,
	"生命加成": 0.03, "速度": 3.0, "效果抵抗": 0.04,
	"效果命中": 0.04, "暴击伤害": 0.04,
}

var allSubAttrs = []string{
	"攻击", "生命", "防御", "防御加成", "暴击", "攻击加成",
	"生命加成", "速度", "效果抵抗", "效果命中", "暴击伤害",
}

func main() {
	inputPath := flag.String("input", "sample.json", "待评估御魂 JSON 文件")
	dataRoot := flag.String("data-root", "", "yuhun 数据目录；默认自动从当前项目定位")
	jsonOutput := flag.Bool("json", false, "以 JSON 输出机器可读报告")
	flag.Parse()

	root, err := resolveDataRoot(*dataRoot)
	if err != nil {
		fatal(err)
	}
	soul, err := loadInput(*inputPath)
	if err != nil {
		fatal(err)
	}
	if err := validateInput(soul); err != nil {
		fatal(err)
	}
	routes, err := loadRoutes(root, soul)
	if err != nil {
		fatal(err)
	}
	pool, err := loadPool(filepath.Join(root, "yys_export", "ios.json"))
	if err != nil {
		fatal(err)
	}

	states := enumerateStates(soul)
	results := make([]routeResult, 0, len(routes))
	for _, r := range routes {
		results = append(results, evaluateRoute(soul, r, pool, states))
	}
	sort.Slice(results, func(i, j int) bool { return results[i].SuccessProb > results[j].SuccessProb })

	if *jsonOutput {
		printJSONReport(soul, results)
		return
	}
	printTextReport(soul, results)
}

func resolveDataRoot(explicit string) (string, error) {
	if explicit != "" {
		return filepath.Abs(explicit)
	}
	candidates := []string{"../yuhun", "yuhun", "../../yuhun"}
	for _, candidate := range candidates {
		if _, err := os.Stat(filepath.Join(candidate, "御魂数据")); err == nil {
			return filepath.Abs(candidate)
		}
	}
	return "", errors.New("未找到 yuhun 数据目录，请使用 -data-root 指定")
}

func loadInput(path string) (inputSoul, error) {
	var soul inputSoul
	b, err := os.ReadFile(path)
	if err != nil {
		return soul, fmt.Errorf("读取输入失败: %w", err)
	}
	if err := json.Unmarshal(b, &soul); err != nil {
		return soul, fmt.Errorf("解析输入 JSON 失败: %w", err)
	}
	return soul, nil
}

func validateInput(s inputSoul) error {
	if s.Type == "" || s.Attributes.Main.Name == "" {
		return errors.New("type 和 attributes.main.name 不能为空")
	}
	if s.Position < 1 || s.Position > 6 {
		return errors.New("position 必须使用 1-6 号位编号")
	}
	if s.Level < 0 || s.Level > 15 || s.Level%3 != 0 {
		return errors.New("level 必须是 0/3/6/9/12/15")
	}
	if len(s.Attributes.Subs) < 2 || len(s.Attributes.Subs) > 4 {
		return errors.New("副属性数量必须为 2-4 条")
	}
	seen := map[string]bool{}
	for _, a := range s.Attributes.Subs {
		if _, ok := attrMax[a.Name]; !ok {
			return fmt.Errorf("未知副属性: %s", a.Name)
		}
		if seen[a.Name] {
			return fmt.Errorf("副属性重复: %s", a.Name)
		}
		seen[a.Name] = true
		if _, err := normalizedValue(a); err != nil {
			return err
		}
	}
	return nil
}

func loadRoutes(root string, soul inputSoul) ([]route, error) {
	var configPath string
	err := filepath.WalkDir(filepath.Join(root, "御魂数据"), func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() && d.Name() == soul.Type+".json" {
			configPath = path
			return filepath.SkipAll
		}
		return nil
	})
	if err != nil || configPath == "" {
		return nil, fmt.Errorf("未找到御魂配置 %s.json", soul.Type)
	}
	b, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}
	var cfg rawConfig
	if err := json.Unmarshal(b, &cfg); err != nil {
		return nil, err
	}

	key := fmt.Sprintf("%d号位", soul.Position)
	if soul.Position == 1 || soul.Position == 3 || soul.Position == 5 {
		key = "135号位"
	}
	raw, ok := cfg.Positions[key]
	if !ok {
		return nil, fmt.Errorf("%s 未配置 %s", soul.Type, key)
	}
	var rr []rawRoute
	if key == "135号位" {
		var pos struct {
			Routes []rawRoute `json:"推荐路线"`
		}
		if err := json.Unmarshal(raw, &pos); err != nil {
			return nil, err
		}
		rr = pos.Routes
	} else {
		var positions []rawPosition
		if err := json.Unmarshal(raw, &positions); err != nil {
			return nil, err
		}
		for _, pos := range positions {
			if normalizeName(pos.Main) == normalizeName(soul.Attributes.Main.Name) {
				rr = pos.Routes
				break
			}
		}
	}
	if len(rr) == 0 {
		return nil, fmt.Errorf("%s %d号位主属性%s没有推荐路线", soul.Type, soul.Position, soul.Attributes.Main.Name)
	}
	result := make([]route, 0, len(rr))
	for _, x := range rr {
		weights := map[string]float64{}
		for i, name := range x.Attrs {
			w := 1.0
			if len(x.Weights) == len(x.Attrs) {
				w = x.Weights[i]
			}
			weights[name] = w
		}
		topN, threshold := x.TopN, x.Threshold
		if topN == 0 {
			topN = 10
		}
		if threshold == 0 {
			threshold = 5.4
		}
		result = append(result, route{x.Name, x.Attrs, weights, topN, threshold, x.Note})
	}
	return result, nil
}

func normalizeName(s string) string {
	switch s {
	case "暴伤":
		return "暴击伤害"
	case "命中":
		return "效果命中"
	case "抵抗":
		return "效果抵抗"
	default:
		return s
	}
}

func loadPool(path string) ([]poolSoul, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取御魂池失败: %w", err)
	}
	var p poolFile
	if err := json.Unmarshal(b, &p); err != nil {
		return nil, err
	}
	return p.Equips, nil
}

func enumerateStates(soul inputSoul) []probabilityState {
	initial := make([]attrState, len(soul.Attributes.Subs))
	for i, a := range soul.Attributes.Subs {
		initial[i] = attrState{Name: a.Name}
	}
	states := []probabilityState{{Attrs: initial, Prob: 1}}
	steps := (15 - soul.Level) / 3
	for step := 0; step < steps; step++ {
		next := map[string]probabilityState{}
		for _, state := range states {
			if len(state.Attrs) < 4 {
				// Until four sub-attributes exist, the roll is drawn from the full
				// secondary-attribute pool (excluding the main attribute). Existing
				// attributes gain a roll; a new attribute is added with that roll.
				choices := possibleAttrs(soul.Attributes.Main.Name)
				for _, name := range choices {
					a := cloneAttrs(state.Attrs)
					found := false
					for i := range a {
						if a[i].Name == name {
							a[i].FutureRolls++
							found = true
							break
						}
					}
					if !found {
						a = append(a, attrState{Name: name, FutureRolls: 1})
					}
					mergeState(next, a, state.Prob/float64(len(choices)))
				}
			} else {
				for i := range state.Attrs {
					a := cloneAttrs(state.Attrs)
					a[i].FutureRolls++
					mergeState(next, a, state.Prob/4)
				}
			}
		}
		states = states[:0]
		for _, state := range next {
			states = append(states, state)
		}
	}
	return states
}

func possibleAttrs(main string) []string {
	var choices []string
	for _, name := range allSubAttrs {
		if name != normalizeName(main) {
			choices = append(choices, name)
		}
	}
	return choices
}

func cloneAttrs(in []attrState) []attrState { return append([]attrState(nil), in...) }

func mergeState(states map[string]probabilityState, attrs []attrState, prob float64) {
	sort.Slice(attrs, func(i, j int) bool { return attrs[i].Name < attrs[j].Name })
	parts := make([]string, len(attrs))
	for i, a := range attrs {
		parts[i] = a.Name + ":" + strconv.Itoa(a.FutureRolls)
	}
	key := strings.Join(parts, "|")
	state := states[key]
	state.Attrs = attrs
	state.Prob += prob
	states[key] = state
}

func evaluateRoute(soul inputSoul, r route, pool []poolSoul, states []probabilityState) routeResult {
	current := scoreInput(soul, r)
	threshold, count := poolThreshold(soul, r, pool)
	if threshold < r.Threshold {
		threshold = r.Threshold
	}
	result := routeResult{Route: r, CurrentScore: current, PoolThreshold: threshold, PoolCount: count, StageThreshold: stageThreshold(soul.Level)}
	result.SuccessProb = probabilityAtLeast(states, soul, r, threshold)
	result.Expected, result.Minimum, result.Maximum = scoreMoments(states, soul, r)
	result.P10 = quantile(states, soul, r, 0.10, result.Minimum, result.Maximum)
	result.P50 = quantile(states, soul, r, 0.50, result.Minimum, result.Maximum)
	result.P90 = quantile(states, soul, r, 0.90, result.Minimum, result.Maximum)
	result.Hits = aggregateHits(states, r)
	seen := map[float64]bool{}
	for _, target := range []float64{1.0, 2.0, 3.0, 4.0, r.Threshold, threshold, 5.4, 6.0} {
		if !seen[target] && target >= result.Minimum-0.001 && target <= result.Maximum+0.001 {
			seen[target] = true
			result.ScoreTargets = append(result.ScoreTargets, targetProbability{target, probabilityAtLeast(states, soul, r, target)})
		}
	}
	sort.Slice(result.ScoreTargets, func(i, j int) bool { return result.ScoreTargets[i].Score < result.ScoreTargets[j].Score })
	return result
}

func scoreInput(soul inputSoul, r route) float64 {
	total := 0.0
	for _, a := range soul.Attributes.Subs {
		if w, ok := r.Weights[a.Name]; ok {
			v, _ := normalizedValue(a)
			total += v * w
		}
	}
	return total
}

func normalizedValue(a inputAttribute) (float64, error) {
	raw := strings.TrimSpace(strings.TrimSuffix(a.Value, "%"))
	v, err := strconv.ParseFloat(raw, 64)
	if err != nil {
		return 0, fmt.Errorf("%s 数值无效: %q", a.Name, a.Value)
	}
	max, ok := attrMax[a.Name]
	if !ok {
		return 0, fmt.Errorf("未知属性: %s", a.Name)
	}
	if strings.Contains(a.Value, "%") {
		v /= 100
	}
	return v / max, nil
}

func poolThreshold(soul inputSoul, r route, pool []poolSoul) (float64, int) {
	var scores []float64
	for _, eq := range pool {
		if eq.Position != soul.Position-1 || eq.Type != soul.Type || normalizeName(eq.Main.Name) != normalizeName(soul.Attributes.Main.Name) {
			continue
		}
		score := 0.0
		for _, a := range eq.Subs {
			w, ok := r.Weights[a.Name]
			if !ok {
				continue
			}
			v, err := normalizedValue(inputAttribute{Name: a.Name, Value: a.Value})
			if err == nil {
				score += v * w
			}
		}
		scores = append(scores, score)
	}
	sort.Sort(sort.Reverse(sort.Float64Slice(scores)))
	if len(scores) == 0 {
		return 0, 0
	}
	index := r.TopN - 1
	if index >= len(scores) {
		index = len(scores) - 1
	}
	return scores[index], len(scores)
}

func fixedAndWeights(state probabilityState, soul inputSoul, r route) (float64, []float64) {
	fixed := scoreInput(soul, r)
	var weights []float64
	for _, a := range state.Attrs {
		w, ok := r.Weights[a.Name]
		if !ok {
			continue
		}
		for i := 0; i < a.FutureRolls; i++ {
			weights = append(weights, w)
		}
	}
	return fixed, weights
}

func probabilityAtLeast(states []probabilityState, soul inputSoul, r route, threshold float64) float64 {
	total := 0.0
	for _, state := range states {
		fixed, weights := fixedAndWeights(state, soul, r)
		if len(weights) == 0 {
			if fixed >= threshold {
				total += state.Prob
			}
			continue
		}
		total += state.Prob * (1 - weightedUniformCDF(threshold, fixed, weights))
	}
	return clamp(total)
}

// Each future roll is Uniform(0.8, 1.0) in normalized units. Inclusion-exclusion
// gives an exact CDF for a weighted sum; there are at most five future rolls.
func weightedUniformCDF(x, fixed float64, weights []float64) float64 {
	if len(weights) == 0 {
		if x < fixed {
			return 0
		}
		return 1
	}
	base, scaleProduct := fixed, 1.0
	for _, w := range weights {
		base += 0.8 * w
		scaleProduct *= 0.2 * w
	}
	y := x - base
	if y <= 0 {
		return 0
	}
	maxY := 0.0
	for _, w := range weights {
		maxY += 0.2 * w
	}
	if y >= maxY {
		return 1
	}
	n := len(weights)
	sum := 0.0
	for mask := 0; mask < (1 << n); mask++ {
		shift, bits := 0.0, 0
		for i, w := range weights {
			if mask&(1<<i) != 0 {
				shift += 0.2 * w
				bits++
			}
		}
		if y > shift {
			term := math.Pow(y-shift, float64(n))
			if bits%2 == 1 {
				sum -= term
			} else {
				sum += term
			}
		}
	}
	return clamp(sum / (factorial(n) * scaleProduct))
}

func factorial(n int) float64 {
	x := 1.0
	for i := 2; i <= n; i++ {
		x *= float64(i)
	}
	return x
}
func clamp(x float64) float64 {
	if x < 0 {
		return 0
	}
	if x > 1 {
		return 1
	}
	return x
}

func scoreMoments(states []probabilityState, soul inputSoul, r route) (float64, float64, float64) {
	expected, minScore, maxScore := 0.0, math.Inf(1), math.Inf(-1)
	for _, state := range states {
		fixed, weights := fixedAndWeights(state, soul, r)
		lo, hi, mean := fixed, fixed, fixed
		for _, w := range weights {
			lo += 0.8 * w
			hi += w
			mean += 0.9 * w
		}
		expected += state.Prob * mean
		if lo < minScore {
			minScore = lo
		}
		if hi > maxScore {
			maxScore = hi
		}
	}
	return expected, minScore, maxScore
}

func quantile(states []probabilityState, soul inputSoul, r route, q, lo, hi float64) float64 {
	for i := 0; i < 60; i++ {
		mid := (lo + hi) / 2
		cdf := 1 - probabilityAtLeast(states, soul, r, mid)
		if cdf < q {
			lo = mid
		} else {
			hi = mid
		}
	}
	return (lo + hi) / 2
}

func aggregateHits(states []probabilityState, r route) []hitDistribution {
	byAttr := map[string]map[int]float64{}
	for _, name := range r.Attrs {
		byAttr[name] = map[int]float64{}
	}
	for _, state := range states {
		counts := map[string]int{}
		for _, a := range state.Attrs {
			counts[a.Name] = a.FutureRolls
		}
		for _, name := range r.Attrs {
			byAttr[name][counts[name]] += state.Prob
		}
	}
	var result []hitDistribution
	for _, name := range r.Attrs {
		result = append(result, hitDistribution{name, byAttr[name]})
	}
	return result
}

func stageThreshold(level int) float64 {
	switch level + 3 {
	case 3:
		return .30
	case 6:
		return .40
	case 9:
		return .50
	case 12:
		return .60
	default:
		return .30
	}
}

func printTextReport(soul inputSoul, results []routeResult) {
	fmt.Printf("御魂强化分析：%s %d号位 +%d\n", soul.Type, soul.Position, soul.Level)
	fmt.Printf("主属性：%s %s；当前副属性：", soul.Attributes.Main.Name, soul.Attributes.Main.Value)
	for i, a := range soul.Attributes.Subs {
		if i > 0 {
			fmt.Print("，")
		}
		fmt.Printf("%s %s", a.Name, a.Value)
	}
	fmt.Println("\n模型：每次强化从排除主属性的副属性池抽取；抽到已有属性则强化，抽到新属性则添加；满4条后各25%强化。每次roll按合法区间均匀分布。")

	best := results[0]
	action := "弃置/不建议投入"
	if best.SuccessProb >= best.StageThreshold {
		action = "继续强化"
	}
	fmt.Printf("\n结论：%s\n", action)
	fmt.Printf("最佳路线：%s；达到动态门槛 %.2f 的概率 %.4f%%，阶段要求 %.0f%%。\n", best.Route.Name, best.PoolThreshold, best.SuccessProb*100, best.StageThreshold*100)
	if best.Maximum+1e-9 < best.PoolThreshold {
		fmt.Printf("关键原因：理论最高分仅 %.2f，低于当前御魂池门槛 %.2f，达标在数学上不可能。\n", best.Maximum, best.PoolThreshold)
	}

	for _, x := range results {
		fmt.Printf("\n[%s] 有效属性=%s\n", x.Route.Name, strings.Join(x.Route.Attrs, "/"))
		fmt.Printf("  当前分 %.3f；期望终分 %.3f；范围 %.3f~%.3f\n", x.CurrentScore, x.Expected, x.Minimum, x.Maximum)
		fmt.Printf("  终分分位数 P10/P50/P90：%.3f / %.3f / %.3f\n", x.P10, x.P50, x.P90)
		fmt.Printf("  同套装同位置同主属性样本 %d；Top %d 动态门槛 %.3f；达标概率 %.6f%%\n", x.PoolCount, x.Route.TopN, x.PoolThreshold, x.SuccessProb*100)
		if x.Route.Note != "" {
			fmt.Printf("  路线说明：%s\n", x.Route.Note)
		}
		fmt.Print("  分数达成概率：")
		for i, p := range x.ScoreTargets {
			if i > 0 {
				fmt.Print("；")
			}
			fmt.Printf("≥%.1f: %.4f%%", p.Score, p.Prob*100)
		}
		fmt.Println()
		for _, h := range x.Hits {
			keys := make([]int, 0, len(h.Probs))
			for k := range h.Probs {
				keys = append(keys, k)
			}
			sort.Ints(keys)
			fmt.Printf("  %s未来获得roll数：", h.Name)
			for i, k := range keys {
				if i > 0 {
					fmt.Print("，")
				}
				fmt.Printf("%d次 %.2f%%", k, h.Probs[k]*100)
			}
			fmt.Println()
		}
	}
	fmt.Println("\n说明：动态门槛取现有 ios.json 中同套装、同位置、同主属性的 Top N 分数与路线最低分的较大值。")
}

func printJSONReport(soul inputSoul, results []routeResult) {
	type jsonResult struct {
		Route              string              `json:"route"`
		EffectiveAttrs     []string            `json:"effective_attributes"`
		CurrentScore       float64             `json:"current_score"`
		Threshold          float64             `json:"threshold"`
		SuccessProbability float64             `json:"success_probability"`
		ExpectedScore      float64             `json:"expected_score"`
		MinScore           float64             `json:"min_score"`
		MaxScore           float64             `json:"max_score"`
		P10                float64             `json:"p10"`
		P50                float64             `json:"p50"`
		P90                float64             `json:"p90"`
		HitDistributions   []hitDistribution   `json:"hit_distributions"`
		ScoreTargets       []targetProbability `json:"score_targets"`
	}
	out := struct {
		Recommendation string       `json:"recommendation"`
		BestRoute      string       `json:"best_route"`
		Results        []jsonResult `json:"results"`
	}{}
	if results[0].SuccessProb >= results[0].StageThreshold {
		out.Recommendation = "继续强化"
	} else {
		out.Recommendation = "弃置"
	}
	out.BestRoute = results[0].Route.Name
	for _, x := range results {
		out.Results = append(out.Results, jsonResult{x.Route.Name, x.Route.Attrs, x.CurrentScore, x.PoolThreshold, x.SuccessProb, x.Expected, x.Minimum, x.Maximum, x.P10, x.P50, x.P90, x.Hits, x.ScoreTargets})
	}
	b, _ := json.MarshalIndent(out, "", "  ")
	fmt.Println(string(b))
}

func fatal(err error) { fmt.Fprintln(os.Stderr, "错误:", err); os.Exit(1) }
