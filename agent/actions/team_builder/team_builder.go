package team_builder

import (
	"encoding/json"
	"fmt"
	"net"
	"sync"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type TeamBuilder struct {
	serverSocket net.Listener
	clientSocket net.Conn
	running      bool
	myID         string
	port         int
	clients      []net.Conn
	messageChan  chan string
	mu           sync.Mutex
}

type TeamBuilderParams struct {
	ID   string `json:"id"`
	Port int    `json:"port"`
}

// Run 执行组队通信
func (a *TeamBuilder) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	fmt.Println("开始执行自定义动作：简单通信")

	params := TeamBuilderParams{}
	if arg.CustomActionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomActionParam), &params); err != nil {
			fmt.Printf("参数解析失败: %v\n", err)
			return false
		}
	}

	if params.ID == "" || params.Port == 0 {
		fmt.Println("无效的参数: 需要提供id和port")
		return false
	}

	a.myID = params.ID
	a.port = params.Port
	a.messageChan = make(chan string, 10)
	a.running = true

	// 尝试作为客户端连接
	isClient := a.connectToServer()

	// 如果客户端连接失败，尝试作为服务器启动
	if !isClient {
		if !a.createServer() {
			fmt.Println("无法创建服务")
			return false
		}

		// 作为服务创建者，也连接到自己的服务
		time.Sleep(500 * time.Millisecond)
		a.connectToServer()
	}

	// 客户端逻辑
	if isClient {
		a.sendMessage("hello")
		select {
		case msg := <-a.messageChan:
			fmt.Printf("已成功连接,准备组队: %s\n", msg)
		case <-time.After(30 * time.Second):
			fmt.Println("等待消息超时")
		}
	} else {
		// 服务器逻辑
		select {
		case msg := <-a.messageChan:
			fmt.Printf("已成功连接,准备组队: %s\n", msg)
			a.sendMessage("you too")
		case <-time.After(300 * time.Second):
			fmt.Println("等待消息超时")
		}
	}

	return true
}

func (a *TeamBuilder) connectToServer() bool {
	a.mu.Lock()
	if a.clientSocket != nil {
		a.clientSocket.Close()
		a.clientSocket = nil
	}
	a.mu.Unlock()

	conn, err := net.Dial("tcp", fmt.Sprintf("localhost:%d", a.port))
	if err != nil {
		fmt.Printf("连接到服务器失败: %v\n", err)
		return false
	}

	a.mu.Lock()
	a.clientSocket = conn
	a.mu.Unlock()

	// 发送自己的ID
	conn.Write([]byte(fmt.Sprintf("ID:%s", a.myID)))

	fmt.Printf("已连接到端口 %d 的服务\n", a.port)
	return true
}

func (a *TeamBuilder) createServer() bool {
	ln, err := net.Listen("tcp", fmt.Sprintf("localhost:%d", a.port))
	if err != nil {
		fmt.Printf("创建服务器失败: %v\n", err)
		return false
	}

	a.mu.Lock()
	a.serverSocket = ln
	a.mu.Unlock()

	fmt.Printf("已创建端口 %d 的服务\n", a.port)

	// 接受连接
	go func() {
		for a.running {
			conn, err := ln.Accept()
			if err != nil {
				continue
			}

			buf := make([]byte, 1024)
			n, err := conn.Read(buf)
			if err != nil {
				conn.Close()
				continue
			}

			data := string(buf[:n])
			if len(data) > 3 && data[:3] == "ID:" {
				clientID := data[3:]
				fmt.Printf("客户端 %s 已连接\n", clientID)

				a.mu.Lock()
				a.clients = append(a.clients, conn)
				a.mu.Unlock()

				go a.handleClient(conn, clientID)
			} else {
				conn.Close()
			}
		}
	}()

	return true
}

func (a *TeamBuilder) handleClient(conn net.Conn, clientID string) {
	buf := make([]byte, 1024)
	for a.running {
		n, err := conn.Read(buf)
		if err != nil {
			break
		}

		message := string(buf[:n])
		a.messageChan <- fmt.Sprintf("%s:%s", clientID, message)
	}

	a.mu.Lock()
	for i, c := range a.clients {
		if c == conn {
			a.clients = append(a.clients[:i], a.clients[i+1:]...)
			break
		}
	}
	a.mu.Unlock()

	conn.Close()
	fmt.Printf("客户端 %s 已断开\n", clientID)
}

func (a *TeamBuilder) sendMessage(message string) bool {
	a.mu.Lock()
	defer a.mu.Unlock()

	if a.clientSocket == nil {
		fmt.Println("未连接到服务器，无法发送消息")
		return false
	}

	_, err := a.clientSocket.Write([]byte(message))
	if err != nil {
		fmt.Printf("发送消息失败: %v\n", err)
		return false
	}

	return true
}