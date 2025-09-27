#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Web Manager - 简单的Web界面管理邮箱账户
基于Flask的轻量级管理界面
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import asyncio
import asyncpg
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

async def get_db_connection():
    """获取数据库连接"""
    try:
        from config import get_db_connection_string
    except Exception:
        import sys, os
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        if repo_root not in sys.path:
            sys.path.append(repo_root)
        from config import get_db_connection_string
    return await asyncpg.connect(get_db_connection_string())

def run_async(coro):
    """运行异步函数的辅助函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Navie 邮箱账户管理</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .stats-container {
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
            gap: 16px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #1d1d1f;
            padding: 24px 20px;
            border-radius: 16px;
            text-align: center;
            min-width: 120px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }
        .stat-card.active {
            background: rgba(52, 199, 89, 0.1);
            border: 1px solid rgba(52, 199, 89, 0.3);
        }
        .stat-card.flagged {
            background: rgba(255, 59, 48, 0.1);
            border: 1px solid rgba(255, 59, 48, 0.3);
        }
        .stat-card.tfa {
            background: rgba(0, 122, 255, 0.1);
            border: 1px solid rgba(0, 122, 255, 0.3);
        }
        .stat-card .stat-number {
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 4px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .stat-card .stat-label {
            font-size: 14px;
            font-weight: 500;
            opacity: 0.8;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .stat-card.active .stat-number { color: #34c759; }
        .stat-card.flagged .stat-number { color: #ff3b30; }
        .stat-card.tfa .stat-number { color: #007aff; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        tr:hover { background-color: #f5f5f5; }
        .current-account { background-color: #e8f5e8; }
        .flagged-row { background-color: #ffe6e6; }
        .btn {
            padding: 8px 16px;
            margin: 4px;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            transition: all 0.2s ease;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }
        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .btn-primary {
            background: rgba(0, 122, 255, 0.9);
            color: white;
            border: 1px solid rgba(0, 122, 255, 0.3);
        }
        .btn-secondary {
            background: rgba(142, 142, 147, 0.9);
            color: white;
            border: 1px solid rgba(142, 142, 147, 0.3);
        }
        .btn-success {
            background: rgba(52, 199, 89, 0.9);
            color: white;
            border: 1px solid rgba(52, 199, 89, 0.3);
        }
        .btn-danger {
            background: rgba(255, 59, 48, 0.9);
            color: white;
            border: 1px solid rgba(255, 59, 48, 0.3);
        }
        .btn-warning {
            background: rgba(255, 204, 0, 0.9);
            color: black;
            border: 1px solid rgba(255, 204, 0, 0.3);
        }
        .btn-info {
            background: rgba(90, 200, 250, 0.9);
            color: white;
            border: 1px solid rgba(90, 200, 250, 0.3);
        }
        .btn-sm {
            padding: 6px 12px;
            font-size: 11px;
            border-radius: 8px;
        }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: white; margin: 5% auto; padding: 20px; border-radius: 8px; width: 80%; max-width: 500px; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: black; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .search-filter-container { margin-bottom: 20px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .provider-badge { padding: 2px 6px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .provider-outlook { background-color: #0078d4; color: white; }
        .provider-gmail { background-color: #ea4335; color: white; }
        .provider-hotmail { background-color: #00bcf2; color: white; }
        .tfa-badge { background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px; }
        .copy-dropdown { position: relative; display: inline-block; }
        .copy-dropdown-content { display: none; position: absolute; background-color: #f9f9f9; min-width: 120px; box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2); z-index: 1; border-radius: 4px; }
        .copy-dropdown-content a { color: black; padding: 8px 12px; text-decoration: none; display: block; font-size: 12px; }
        .copy-dropdown-content a:hover { background-color: #f1f1f1; }
        .copy-dropdown:hover .copy-dropdown-content { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📧 Navie 邮箱账户管理</h1>
        
        <!-- 统计信息 -->
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_accounts or 0 }}</div>
                <div class="stat-label">总账户</div>
            </div>
            <div class="stat-card active">
                <div class="stat-number">{{ stats.active_accounts or 0 }}</div>
                <div class="stat-label">活跃账户</div>
            </div>
            <div class="stat-card flagged">
                <div class="stat-number">{{ stats.flagged_accounts or 0 }}</div>
                <div class="stat-label">已标记</div>
            </div>
            <div class="stat-card tfa">
                <div class="stat-number">{{ stats.tfa_accounts or 0 }}</div>
                <div class="stat-label">2FA账户</div>
            </div>
        </div>
        
        <!-- 操作按钮 -->
        <div style="margin-bottom: 24px; display: flex; gap: 12px; flex-wrap: wrap;">
            <button onclick="showAddAccountModal()" class="btn btn-primary">➕ 添加账户</button>
            <button onclick="refreshAccounts()" class="btn btn-secondary">🔄 刷新</button>
            <button onclick="exportAccounts()" class="btn btn-info">📤 导出</button>
            <button onclick="importAccounts()" class="btn btn-warning">📥 导入</button>
        </div>

        <!-- 搜索和筛选 -->
        <div class="search-filter-container">
            <input type="text" id="searchInput" placeholder="搜索邮箱地址..." onkeyup="filterTable()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 200px;">
            <select id="providerFilter" onchange="filterTable()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                <option value="">所有提供商</option>
                <option value="outlook">Outlook</option>
                <option value="gmail">Gmail</option>
                <option value="hotmail">Hotmail</option>
            </select>
            <select id="tfaFilter" onchange="filterTable()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                <option value="">所有2FA状态</option>
                <option value="yes">有2FA</option>
                <option value="no">无2FA</option>
            </select>
            <select id="flagFilter" onchange="filterTable()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                <option value="">所有标记状态</option>
                <option value="flagged">已标记</option>
                <option value="normal">正常</option>
            </select>
            <select id="timeFilter" onchange="filterTable()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                <option value="">所有时间</option>
                <option value="week">一周以上</option>
                <option value="month">一个月以上</option>
                <option value="never">从未使用</option>
            </select>
            <button onclick="clearFilters()" class="btn btn-secondary" style="padding: 8px 12px;">清除筛选</button>
        </div>
        
        <!-- 账户列表 -->
        <table id="accountsTable">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>邮箱地址</th>
                    <th>提供商</th>
                    <th>2FA</th>
                    <th>标记状态</th>
                    <th>使用次数</th>
                    <th>最后使用</th>
                    <th>创建时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                {% for account in accounts %}
                <tr class="{% if account.is_flagged %}flagged-row{% endif %} {% if loop.index0 == current_index %}current-account{% endif %}">
                    <td>{{ loop.index }}</td>
                    <td>
                        {{ account.email }}
                        {% if loop.index0 == current_index %}<span style="color: #28a745;">← 当前</span>{% endif %}
                    </td>
                    <td><span class="provider-badge provider-{{ account.provider }}">{{ account.provider.upper() }}</span></td>
                    <td>{% if account.tfa_secret %}<span class="tfa-badge">2FA</span>{% endif %}</td>
                    <td>
                        {% if account.is_flagged %}
                            <span style="color: #dc3545;">🚩 {{ account.flag_reason or '已标记' }}</span>
                        {% else %}
                            <span style="color: #28a745;">✓ 正常</span>
                        {% endif %}
                    </td>
                    <td>{{ account.usage_count or 0 }}</td>
                    <td>{{ account.last_used_at.strftime('%Y-%m-%d %H:%M') if account.last_used_at else '从未使用' }}</td>
                    <td>{{ account.created_at.strftime('%Y-%m-%d %H:%M') if account.created_at else '' }}</td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="setCurrent({{ loop.index0 }})">设为当前</button>
                        {% if account.is_flagged %}
                            <button class="btn btn-success btn-sm" onclick="unflagAccount({{ account.id }})">取消标记</button>
                        {% else %}
                            <button class="btn btn-danger btn-sm" onclick="flagAccount({{ account.id }})">标记</button>
                        {% endif %}
                        <button class="btn btn-secondary btn-sm" onclick="editAccount({{ account.id }})">编辑</button>
                        <button class="btn btn-info btn-sm" onclick="githubLogin('{{ account.email }}', '{{ account.password }}', '{{ account.tfa_secret or '' }}')">GitHub登录</button>
                        <div class="copy-dropdown">
                            <button class="btn btn-primary btn-sm">📋 复制</button>
                            <div class="copy-dropdown-content">
                                <a href="#" onclick="copyToClipboard('{{ account.email }}', '邮箱地址'); return false;">复制邮箱</a>
                                <a href="#" onclick="copyToClipboard('{{ account.password }}', '邮箱密码'); return false;">复制邮箱密码</a>
                                <a href="#" onclick="copyToClipboard('{{ account.password }}', 'GitHub密码'); return false;">复制GitHub密码</a>
                                {% if account.tfa_secret %}
                                <a href="#" onclick="copyToClipboard('{{ account.tfa_secret }}', '2FA密钥'); return false;">复制2FA</a>
                                {% endif %}
                                <a href="#" onclick="copyAccountInfo({{ account.id }}); return false;">复制全部信息</a>
                            </div>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- 添加账户模态框 -->
    <div id="addModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('addModal')">&times;</span>
            <h2>添加新账户</h2>
            <form id="addForm">
                <div class="form-group">
                    <label for="addEmail">邮箱地址:</label>
                    <input type="email" id="addEmail" name="email" required>
                </div>
                <div class="form-group">
                    <label for="addPassword">密码:</label>
                    <input type="password" id="addPassword" name="password" required>
                </div>
                <div class="form-group">
                    <label for="addClientId">Client ID:</label>
                    <input type="text" id="addClientId" name="client_id">
                </div>
                <div class="form-group">
                    <label for="addAccessToken">Access Token:</label>
                    <input type="text" id="addAccessToken" name="access_token">
                </div>
                <div class="form-group">
                    <label for="addTfaSecret">2FA密钥:</label>
                    <input type="text" id="addTfaSecret" name="tfa_secret">
                </div>
                <div class="form-group">
                    <label for="addProvider">提供商:</label>
                    <select id="addProvider" name="provider">
                        <option value="outlook">Outlook</option>
                        <option value="gmail">Gmail</option>
                        <option value="hotmail">Hotmail</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">添加账户</button>
            </form>
        </div>
    </div>

    <!-- 编辑账户模态框 -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('editModal')">&times;</span>
            <h2>编辑账户</h2>
            <form id="editForm">
                <input type="hidden" id="editAccountId" name="account_id">
                <div class="form-group">
                    <label for="editEmail">邮箱地址:</label>
                    <input type="email" id="editEmail" name="email" required>
                </div>
                <div class="form-group">
                    <label for="editPassword">密码:</label>
                    <input type="password" id="editPassword" name="password" required>
                </div>
                <div class="form-group">
                    <label for="editClientId">Client ID:</label>
                    <input type="text" id="editClientId" name="client_id">
                </div>
                <div class="form-group">
                    <label for="editAccessToken">Access Token:</label>
                    <input type="text" id="editAccessToken" name="access_token">
                </div>
                <div class="form-group">
                    <label for="editTfaSecret">2FA密钥:</label>
                    <input type="text" id="editTfaSecret" name="tfa_secret">
                </div>
                <div class="form-group">
                    <label for="editProvider">提供商:</label>
                    <select id="editProvider" name="provider">
                        <option value="outlook">Outlook</option>
                        <option value="gmail">Gmail</option>
                        <option value="hotmail">Hotmail</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">保存修改</button>
            </form>
        </div>
    </div>

    <script>
        // 搜索和筛选功能
        function filterTable() {
            const searchInput = document.getElementById('searchInput');
            const providerFilter = document.getElementById('providerFilter');
            const tfaFilter = document.getElementById('tfaFilter');
            const flagFilter = document.getElementById('flagFilter');
            const timeFilter = document.getElementById('timeFilter');

            const searchTerm = searchInput.value.toLowerCase();
            const providerValue = providerFilter.value.toLowerCase();
            const tfaValue = tfaFilter.value;
            const flagValue = flagFilter.value;
            const timeValue = timeFilter.value;

            const table = document.getElementById('accountsTable');
            const rows = table.getElementsByTagName('tr');

            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const cells = row.getElementsByTagName('td');

                // 获取各列的值
                const email = cells[1] ? (cells[1].textContent || cells[1].innerText).toLowerCase() : '';
                const provider = cells[2] ? (cells[2].textContent || cells[2].innerText).toLowerCase() : '';
                const hasTfa = cells[3] ? (cells[3].textContent || cells[3].innerText).includes('2FA') : false;
                const isFlagged = row.classList.contains('flagged-row');
                const createdAt = cells[7] ? (cells[7].textContent || cells[7].innerText).trim() : '';

                // 应用筛选条件
                let showRow = true;

                // 搜索筛选
                if (searchTerm && email.indexOf(searchTerm) === -1) {
                    showRow = false;
                }

                // 提供商筛选
                if (providerValue && provider.indexOf(providerValue) === -1) {
                    showRow = false;
                }

                // 2FA筛选
                if (tfaValue === 'yes' && !hasTfa) {
                    showRow = false;
                } else if (tfaValue === 'no' && hasTfa) {
                    showRow = false;
                }

                // 标记状态筛选
                if (flagValue === 'flagged' && !isFlagged) {
                    showRow = false;
                } else if (flagValue === 'normal' && isFlagged) {
                    showRow = false;
                }

                // 时间筛选（基于创建时间）
                if (timeValue && createdAt) {
                    const now = new Date();
                    try {
                        const createdDate = new Date(createdAt.replace(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})/, '$1/$2/$3 $4:$5'));

                        if (timeValue === 'week') {
                            // 一周以上
                            const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                            if (createdDate > weekAgo) {
                                showRow = false;
                            }
                        } else if (timeValue === 'month') {
                            // 一个月以上
                            const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                            if (createdDate > monthAgo) {
                                showRow = false;
                            }
                        }
                    } catch (e) {
                        // 解析失败，保持显示
                        console.warn('时间解析失败:', createdAt, e);
                    }
                } else if (timeValue === 'never') {
                    // 从未使用 - 检查最后使用时间
                    const lastUsed = cells[6] ? (cells[6].textContent || cells[6].innerText).trim() : '';
                    if (lastUsed !== '从未使用') {
                        showRow = false;
                    }
                }

                row.style.display = showRow ? '' : 'none';
            }
        }

        // 清除所有筛选
        function clearFilters() {
            document.getElementById('searchInput').value = '';
            document.getElementById('providerFilter').value = '';
            document.getElementById('tfaFilter').value = '';
            document.getElementById('flagFilter').value = '';
            document.getElementById('timeFilter').value = '';
            filterTable();
        }

        // 复制到剪贴板
        function copyToClipboard(text, type) {
            navigator.clipboard.writeText(text).then(function() {
                alert(type + ' 已复制到剪贴板');
            }, function(err) {
                console.error('复制失败: ', err);
                alert('复制失败，请手动复制');
            });
        }

        // 复制账户完整信息
        function copyAccountInfo(accountId) {
            fetch(`/get_account/${accountId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const account = data.data;
                        const info = `邮箱: ${account.email}
密码: ${account.password}
Client ID: ${account.client_id || ''}
Access Token: ${account.access_token || ''}
2FA密钥: ${account.tfa_secret || ''}
提供商: ${account.provider}`;
                        copyToClipboard(info, '账户完整信息');
                    } else {
                        alert('获取账户信息失败');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('获取账户信息失败');
                });
        }

        // GitHub登录
        function githubLogin(email, password, tfaSecret) {
            if (!email || !password) {
                alert('邮箱和密码不能为空');
                return;
            }

            const loginData = {
                username: email,
                password: password,
                tfa_secret: tfaSecret || '',
                headless: false
            };

            fetch('/api/github/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(loginData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('GitHub登录成功！');
                    refreshAccounts(); // 刷新页面以更新使用记录
                } else {
                    alert('GitHub登录失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('GitHub登录请求失败');
            });
        }

        // 模态框相关函数
        function showAddAccountModal() {
            document.getElementById('addModal').style.display = 'block';
        }

        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }

        // 刷新页面
        function refreshAccounts() {
            location.reload();
        }

        // 设为当前账户
        function setCurrent(index) {
            fetch('/set_current', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({index: index})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    refreshAccounts();
                } else {
                    alert('设置失败');
                }
            });
        }

        // 标记账户
        function flagAccount(accountId) {
            const reason = prompt('请输入标记原因:');
            if (reason !== null) {
                fetch('/flag_account', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({account_id: accountId, reason: reason})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        refreshAccounts();
                    } else {
                        alert('标记失败');
                    }
                });
            }
        }

        // 取消标记账户
        function unflagAccount(accountId) {
            fetch('/unflag_account', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({account_id: accountId})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    refreshAccounts();
                } else {
                    alert('取消标记失败');
                }
            });
        }

        // 编辑账户
        function editAccount(accountId) {
            fetch(`/get_account/${accountId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const account = data.data;
                        document.getElementById('editAccountId').value = account.id;
                        document.getElementById('editEmail').value = account.email;
                        document.getElementById('editPassword').value = account.password;
                        document.getElementById('editClientId').value = account.client_id || '';
                        document.getElementById('editAccessToken').value = account.access_token || '';
                        document.getElementById('editTfaSecret').value = account.tfa_secret || '';
                        document.getElementById('editProvider').value = account.provider;
                        document.getElementById('editModal').style.display = 'block';
                    } else {
                        alert('获取账户信息失败');
                    }
                });
        }

        // 表单提交处理
        document.getElementById('addForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            fetch('/add_account', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    closeModal('addModal');
                    refreshAccounts();
                } else {
                    alert('添加账户失败');
                }
            });
        });

        document.getElementById('editForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            fetch('/edit_account', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    closeModal('editModal');
                    refreshAccounts();
                } else {
                    alert('编辑账户失败');
                }
            });
        });

        // 导出和导入功能（占位符）
        function exportAccounts() {
            alert('导出功能开发中...');
        }

        function importAccounts() {
            alert('导入功能开发中...');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页面"""
    async def get_data():
        conn = await get_db_connection()
        try:
            # 获取所有账户
            accounts = await conn.fetch("""
                SELECT id, email, password, client_id, access_token, tfa_secret,
                       is_flagged, flag_reason, provider, usage_count,
                       last_used_at, created_at
                FROM email_accounts
                WHERE is_active = true
                ORDER BY created_at ASC
            """)

            # 获取当前账户索引
            current_index = await conn.fetchval("""
                SELECT config_value FROM email_config
                WHERE config_key = 'current_account_index'
            """)
            current_index = int(current_index) if current_index else 0

            # 获取统计信息
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_accounts,
                    COUNT(*) FILTER (WHERE is_active = true) as active_accounts,
                    COUNT(*) FILTER (WHERE is_flagged = true) as flagged_accounts,
                    COUNT(*) FILTER (WHERE tfa_secret IS NOT NULL) as tfa_accounts
                FROM email_accounts
            """)

            return list(accounts), current_index, dict(stats)
        finally:
            await conn.close()

    accounts, current_index, stats = run_async(get_data())

    return render_template_string(HTML_TEMPLATE,
                                accounts=accounts,
                                current_index=current_index,
                                stats=stats)

@app.route('/add_account', methods=['POST'])
def add_account():
    """添加账户"""
    data = request.json

    async def add_account_async():
        conn = await get_db_connection()
        try:
            await conn.execute("""
                INSERT INTO email_accounts (email, password, client_id, access_token, tfa_secret, provider)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (email) DO UPDATE SET
                    password = EXCLUDED.password,
                    client_id = EXCLUDED.client_id,
                    access_token = EXCLUDED.access_token,
                    tfa_secret = EXCLUDED.tfa_secret,
                    provider = EXCLUDED.provider,
                    updated_at = CURRENT_TIMESTAMP
            """, data['email'], data['password'], data['client_id'],
                 data.get('access_token') or None, data.get('tfa_secret') or None,
                 data.get('provider', 'outlook'))
            return True
        except Exception as e:
            logger.error(f"添加账户失败: {e}")
            return False
        finally:
            await conn.close()

    success = run_async(add_account_async())
    return jsonify({'success': success})

@app.route('/set_current', methods=['POST'])
def set_current():
    """设置当前账户"""
    data = request.json
    index = data['index']

    async def set_current_async():
        conn = await get_db_connection()
        try:
            await conn.execute("""
                INSERT INTO email_config (config_key, config_value)
                VALUES ('current_account_index', $1)
                ON CONFLICT (config_key)
                DO UPDATE SET config_value = EXCLUDED.config_value, updated_at = CURRENT_TIMESTAMP
            """, str(index))
            return True
        except Exception as e:
            logger.error(f"设置当前账户失败: {e}")
            return False
        finally:
            await conn.close()

    success = run_async(set_current_async())
    return jsonify({'success': success})

@app.route('/flag_account', methods=['POST'])
def flag_account():
    """标记账户"""
    data = request.json

    async def flag_account_async():
        conn = await get_db_connection()
        try:
            await conn.execute("""
                UPDATE email_accounts
                SET is_flagged = true, flag_reason = $2, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, data['account_id'], data['reason'])
            return True
        except Exception as e:
            logger.error(f"标记账户失败: {e}")
            return False
        finally:
            await conn.close()

    success = run_async(flag_account_async())
    return jsonify({'success': success})

@app.route('/unflag_account', methods=['POST'])
def unflag_account():
    """取消标记账户"""
    data = request.json

    async def unflag_account_async():
        conn = await get_db_connection()
        try:
            await conn.execute("""
                UPDATE email_accounts
                SET is_flagged = false, flag_reason = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, data['account_id'])
            return True
        except Exception as e:
            logger.error(f"取消标记账户失败: {e}")
            return False
        finally:
            await conn.close()

    success = run_async(unflag_account_async())
    return jsonify({'success': success})

@app.route('/get_account/<int:account_id>')
def get_account(account_id):
    """获取账户信息"""
    async def get_account_async():
        conn = await get_db_connection()
        try:
            account = await conn.fetchrow("""
                SELECT id, email, password, client_id, access_token, tfa_secret, provider
                FROM email_accounts
                WHERE id = $1 AND is_active = true
            """, account_id)

            if account:
                return dict(account)
            else:
                return None
        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            return None
        finally:
            await conn.close()

    account = run_async(get_account_async())
    if account:
        return jsonify({'success': True, 'data': account})
    else:
        return jsonify({'success': False, 'message': '账户不存在'})

@app.route('/edit_account', methods=['POST'])
def edit_account():
    """编辑账户"""
    data = request.json

    async def edit_account_async():
        conn = await get_db_connection()
        try:
            await conn.execute("""
                UPDATE email_accounts
                SET email = $2, password = $3, client_id = $4, access_token = $5,
                    tfa_secret = $6, provider = $7, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, data['account_id'], data['email'], data['password'], data['client_id'],
                 data.get('access_token') or None, data.get('tfa_secret') or None,
                 data.get('provider', 'outlook'))
            return True
        except Exception as e:
            logger.error(f"编辑账户失败: {e}")
            return False
        finally:
            await conn.close()

    success = run_async(edit_account_async())
    return jsonify({'success': success})

@app.route('/api/github/login', methods=['POST'])
def github_login():
    """GitHub登录接口"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    tfa_secret = data.get('tfa_secret')
    headless = data.get('headless', False)

    if not username or not password:
        return jsonify({
            'success': False,
            'message': '用户名和密码不能为空'
        })

    try:
        # 导入GitHub登录脚本
        import subprocess
        import json
        import os

        # 构建命令
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts', 'github_login.py')
        cmd = ['python', script_path, username, password]

        if tfa_secret:
            cmd.append(tfa_secret)
        else:
            cmd.append('')  # 占位符

        cmd.append('true' if headless else 'false')

        logger.info(f"执行GitHub登录命令: {' '.join(cmd[:3])} [密码已隐藏] ...")

        # 执行登录脚本
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2分钟超时
        )

        logger.info(f"GitHub登录脚本执行完成，返回码: {result.returncode}")
        logger.info(f"标准输出: {result.stdout}")
        if result.stderr:
            logger.error(f"标准错误: {result.stderr}")

        if result.returncode == 0:
            # 解析返回结果
            try:
                login_result = json.loads(result.stdout)

                # 如果登录成功，更新数据库中的使用记录
                if login_result.get('success'):
                    async def update_usage():
                        conn = await get_db_connection()
                        try:
                            # 根据用户名（邮箱）更新使用记录
                            await conn.execute("""
                                UPDATE email_accounts
                                SET usage_count = COALESCE(usage_count, 0) + 1,
                                    last_used_at = CURRENT_TIMESTAMP,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE email = $1 AND is_active = true
                            """, username)
                            logger.info(f"已更新GitHub登录使用记录: {username}")
                        except Exception as e:
                            logger.error(f"更新使用记录失败: {e}")
                        finally:
                            await conn.close()

                    # 异步更新数据库
                    run_async(update_usage())

                return jsonify(login_result)
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'message': f'登录脚本返回格式错误: {result.stdout}'
                })
        else:
            return jsonify({
                'success': False,
                'message': f'登录脚本执行失败: {result.stderr}'
            })

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': '登录超时，请重试'
        })
    except Exception as e:
        logger.error(f"GitHub登录异常: {e}")
        return jsonify({
            'success': False,
            'message': f'登录异常: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
