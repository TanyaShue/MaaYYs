package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"maa-yys-agent/projectinterface"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

var Version = "1.0.0"

func main() {
	log.Info().
		Str("version", Version).
		Msg("MaaYYs Agent Service")

	// ProjectInterface clients append the generated Agent identifier to the
	// configured child_args when starting the child process.
	socketID, err := agentIdentifier(os.Args)
	if err != nil {
		log.Fatal().Err(err).Msg("Missing agent identifier")
	}

	log.Info().
		Str("socketID", socketID).
		Msg("Starting agent server")

	// 初始化MAA框架
	libDir := maafwLibDir()
	log.Info().
		Str("libDir", libDir).
		Msg("Initializing MAA framework")
	if err := maa.Init(maa.WithLibDir(libDir)); err != nil {
		log.Fatal().
			Err(err).
			Msg("Failed to initialize MAA framework")
	}
	defer func() {
		if err := maa.Release(); err != nil {
			log.Error().Err(err).Msg("Failed to release MAA framework")
		}
	}()
	log.Info().Msg("MAA framework initialized")

	piContext, err := projectinterface.Load()
	if err != nil {
		log.Warn().Err(err).Msg("Invalid ProjectInterface agent context")
	} else {
		log.Info().
			Str("piVersion", piContext.InterfaceVersion).
			Str("client", piContext.ClientName).
			Str("clientVersion", piContext.ClientVersion).
			Str("language", piContext.ClientLanguage).
			Str("maaFrameworkVersion", piContext.ClientMaaFW).
			Str("projectVersion", piContext.ProjectVersion).
			Interface("controller", piContext.Controller).
			Interface("resource", piContext.Resource).
			Msg("ProjectInterface agent context loaded")
	}

	// 初始化Toolkit配置选项
	userPath := getCwd()
	if err := maa.ConfigInitOption(userPath, "{}"); err != nil {
		log.Warn().
			Str("userPath", userPath).
			Err(err).
			Msg("Failed to init toolkit config option")
	} else {
		log.Info().
			Str("userPath", userPath).
			Msg("Toolkit config option initialized")
	}

	// 注册所有 custom actions 和 recognitions
	if err := registerAll(); err != nil {
		log.Fatal().Err(err).Msg("Failed to register custom runners")
	}

	// 启动Agent Server
	if err := maa.AgentServerStartUp(socketID); err != nil {
		log.Fatal().
			Err(err).
			Msg("Failed to start agent server")
	}
	log.Info().Msg("Agent server started")

	// 等待服务器完成
	maa.AgentServerJoin()

	// 关闭
	maa.AgentServerShutDown()
	log.Info().Msg("Agent server shutdown")
}

func getCwd() string {
	cwd, err := os.Getwd()
	if err != nil {
		return "."
	}
	return cwd
}

// maafwLibDir 决定去哪里加载 MaaFramework 动态库。
//
// 桌面端发行包的布局是 <cwd>/maafw/*，保持默认即可。
// Android 上库位于 APK 的 nativeLibraryDir，cwd 不由我们掌控，所以用
// MAAFW_LIB_DIR 覆盖；显式设为空字符串时只传库名，交给 LD_LIBRARY_PATH 解析。
func maafwLibDir() string {
	if override, ok := os.LookupEnv("MAAFW_LIB_DIR"); ok {
		return strings.TrimSpace(override)
	}
	return filepath.Join(getCwd(), "maafw")
}

func agentIdentifier(args []string) (string, error) {
	if len(args) < 2 || strings.TrimSpace(args[1]) == "" {
		return "", fmt.Errorf("usage: %s <identifier>", filepath.Base(args[0]))
	}
	return args[1], nil
}
