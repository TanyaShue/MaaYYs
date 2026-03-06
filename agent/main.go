package main

import (
	"os"
	"path/filepath"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

var Version = "1.0.0"

func main() {
	log.Info().
		Str("version", Version).
		Msg("MaaYYs Agent Service")

	// 获取socket ID
	socketID := "maa-agent-server"
	if len(os.Args) > 1 {
		socketID = os.Args[1]
	}

	log.Info().
		Str("socketID", socketID).
		Msg("Starting agent server")

	// 初始化MAA框架
	libDir := filepath.Join(getCwd(), "maafw")
	log.Info().
		Str("libDir", libDir).
		Msg("Initializing MAA framework")
	if err := maa.Init(maa.WithLibDir(libDir)); err != nil {
		log.Fatal().
			Err(err).
			Msg("Failed to initialize MAA framework")
	}
	defer maa.Release()
	log.Info().Msg("MAA framework initialized")

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

	// 注册所有custom actions和recognitions
	registerAll()

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