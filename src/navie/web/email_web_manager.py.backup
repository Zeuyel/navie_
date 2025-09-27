#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Web Manager - 缂備胶濮崑鎾绘煕濡や焦绀堟繛鍫熷弴eb闂佷紮绲介惌鍌氼焽閹殿喚涓嶉柨娑樺閸婄偤姊洪褍鏋ゆい鏂跨墢閹峰綊鏁傞挊澶屽幈
闂佺硶鏅炲銊ц姳閻濈穱ask闂佹眹鍔岀€氼垱绂嶉妶澶嬬厒闊洦娲熼悰鎾剁磼閻欏懐纾块柟顔硷躬閹儳鐣濋崟顒併€?
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import asyncio
import asyncpg
from datetime import datetime
import logging

# 闂備焦婢樼粔鍫曟偪閸℃稑绫嶉柕澶堝劤缁?
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

async def get_db_connection():
    """Return an asyncpg connection. Also works when run directly."""
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
    """闁哄鏅滈崝姗€銆侀幋婵愬殨闁稿本渚楅崝鍕煕閹达絽袚闁?""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# HTML濠碘槅鍨崜婵嗩熆?HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Navie 闂備緡鍙庨崰姘额敊閸垻涓嶉柨娑樺閸婄偤鏌?/title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .stats { display: flex; justify-content: space-around; margin-bottom: 30px; }
        .stat-card { background: #007bff; color: white; padding: 15px; border-radius: 5px; text-align: center; min-width: 120px; }
        .stat-card.flagged { background: #dc3545; }
        .stat-card.tfa { background: #28a745; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        tr:hover { background-color: #f5f5f5; }
        .btn { padding: 6px 12px; margin: 2px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-danger { background-color: #dc3545; color: white; }
        .btn-success { background-color: #28a745; color: white; }
        .btn-warning { background-color: #ffc107; color: black; }
        .btn-secondary { background-color: #6c757d; color: white; }
        .btn:hover { opacity: 0.8; }
        .flagged-row { background-color: #fff5f5; }
        .current-account { background-color: #e8f5e8; font-weight: bold; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: white; margin: 5% auto; padding: 20px; border-radius: 8px; width: 80%; max-width: 600px; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: black; }
        .search-box { margin-bottom: 20px; }
        .search-box input { width: 300px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .provider-badge { padding: 2px 6px; border-radius: 3px; font-size: 12px; }
        .provider-outlook { background-color: #0078d4; color: white; }
        .provider-hotmail { background-color: #0078d4; color: white; }
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
        <h1>濡絽鍟幉?Navie 闂備緡鍙庨崰姘额敊閸垻涓嶉柨娑樺閸婄偤鏌?/h1>
        
        <!-- 缂傚倷鑳堕崰鏇㈩敇閸涘﹦鈹嶉柍鈺佸暕缁?-->
        <div class="stats">
            <div class="stat-card">
                <div style="font-size: 24px;">{{ stats.total_accounts or 0 }}</div>
                <div>闂佽鍓氬Σ鎺撳緞閸曨垰绠?/div>
            </div>
            <div class="stat-card">
                <div style="font-size: 24px;">{{ stats.active_accounts or 0 }}</div>
                <div>濠电偛寮跺Σ鎺旂矚椤掑倹瀚婚柨鏃囨閻?/div>
            </div>
            <div class="stat-card flagged">
                <div style="font-size: 24px;">{{ stats.flagged_accounts or 0 }}</div>
                <div>閻庡湱顭堝鍫曟偉閿濆洦濯?/div>
            </div>
            <div class="stat-card tfa">
                <div style="font-size: 24px;">{{ stats.tfa_accounts or 0 }}</div>
                <div>2FA闁荤姵鍔ч梽鍕春?/div>
            </div>
        </div>
        
        <!-- 闂佺懓鐏濈粔宕囩礊閺冨牆绠板鑸靛姈鐏?-->
        <div style="margin-bottom: 20px;">
            <button class="btn btn-primary" onclick="showAddModal()">闂?濠电儑缍€椤曆勬叏閻愬灚瀚婚柨鏃囨閻?/button>
            <button class="btn btn-secondary" onclick="location.reload()">濡絽鍟弫?闂佸憡甯￠弨閬嶅蓟?/button>
            <button class="btn btn-primary" onclick="window.open('/env_config', '_blank')">闂佽櫕瀵ч悷杈╃箔?闂佺粯绮犻崹浼淬€傞妸鈺佺煑婵せ鍋撻柛锝嗘そ閺屽﹤顓奸崶鈺傜€?/button>
            <button class="btn btn-success" onclick="window.open('/email_fetch', '_blank')">濡絽鍟幉?闂備緡鍙庨崰姘额敊閸儱鐭楅柡宓啫鈻?/button>
        </div>
        
        <!-- 闂佺懓鍚嬬划搴ㄥ磼閵娾晛妞界€光偓閳ь剟鎮洪锔界劵濠㈣泛顑愰弨?-->
        <div class="search-filter-box" style="display: flex; gap: 15px; margin-bottom: 20px; align-items: center;">
            <div class="search-box" style="flex: 1;">
                <input type="text" id="searchInput" placeholder="闂佺懓鍚嬬划搴ㄥ磼閵娾晜鐒芥い鏃傝檸閸炴悂鏌涢敂鑺ョ凡婵?.." onkeyup="filterTable()" style="width: 100%;">
            </div>
            <div class="filter-box" style="display: flex; gap: 10px;">
                <select id="providerFilter" onchange="filterTable()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    <option value="">闂佸湱顣介崑鎾绘煛閸繍妲圭憸棰佺劍缁楃喎鈽夊Ο缁樼彍</option>
                    <option value="outlook">Outlook</option>
                    <option value="hotmail">Hotmail</option>
                </select>
                <select id="tfaFilter" onchange="filterTable()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    <option value="">闂佸湱顣介崑鎾绘煛?FA闂佺粯顭堥崺鏍焵?/option>
                    <option value="yes">闂?FA</option>
                    <option value="no">闂?FA</option>
                </select>
                <select id="flagFilter" onchange="filterTable()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    <option value="">闂佸湱顣介崑鎾绘煛閸繍妲归柣鏍电悼閹峰骞嶉澶癸箓鏌?/option>
                    <option value="flagged">閻庡湱顭堝鍫曟偉閿濆洦濯?/option>
                    <option value="normal">濠殿喗绻愮徊浠嬫偉?/option>
                </select>
                <select id="timeFilter" onchange="filterTable()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    <option value="">闂佸湱顣介崑鎾绘煛閸繍妲规俊鐐插€垮?/option>
                    <option value="week">婵炴垶鎸撮崑鎾绘煕濞戞牕濡哄ù婊勫笚缁?/option>
                    <option value="month">婵炴垶鎸撮崑鎾斥槈閹垮啩绨兼繝鈧埀顒€霉閻橆喖鍔欑紒?/option>
                    <option value="never">婵炲濮寸€涒晛锕㈤鐔稿閻犳亽鍔嶉弳?/option>
                </select>
                <button onclick="clearFilters()" class="btn btn-secondary" style="padding: 8px 12px;">濠电偞鎸搁幊妯衡枍鎼达絿椹虫繛鎴旀噰閸?/button>
            </div>
        </div>
        
        <!-- 闁荤姵鍔ч梽鍕春濞戙垹绀嗘俊銈呭閳?-->
        <table id="accountsTable">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>闂備緡鍙庨崰姘额敊閸儱鎹堕柡澶嬪缁?/th>
                    <th>闂佸湱绮崝鎺旀閻㈢鐤?/th>
                    <th>2FA</th>
                    <th>闂佸搫绉村ú鈺咁敊閸ヮ剚鍋愰柤鍝ヮ暯閸?/th>
                    <th>婵炶揪缍€濞夋洟寮妶鍛瀻闁斥晛鍟▓?/th>
                    <th>闂佸搫鐗冮崑鎾绘煕濮橆剛鍑瑰┑鐐叉喘閹?/th>
                    <th>闂佸憡甯楃粙鎴犵磽閹捐绫嶉柛顐ｆ礃閿?/th>
                    <th>闂佺懓鐏濈粔宕囩礊?/th>
                </tr>
            </thead>
            <tbody>
                {% for account in accounts %}
                <tr class="{% if account.is_flagged %}flagged-row{% endif %} {% if loop.index0 == current_index %}current-account{% endif %}">
                    <td>{{ account.id }}</td>
                    <td>
                        {{ account.email }}
                        {% if loop.index0 == current_index %}<span style="color: #28a745;">闂?閻熸粎澧楅幐鍛婃櫠?/span>{% endif %}
                    </td>
                    <td><span class="provider-badge provider-{{ account.provider }}">{{ account.provider.upper() }}</span></td>
                    <td>{% if account.tfa_secret %}<span class="tfa-badge">2FA</span>{% endif %}</td>
                    <td>
                        {% if account.is_flagged %}
                            <span style="color: #dc3545;">濡絽鍟惁?{{ account.flag_reason or '閻庡湱顭堝鍫曟偉閿濆洦濯? }}</span>
                        {% else %}
                            <span style="color: #28a745;">闂?濠殿喗绻愮徊浠嬫偉?/span>
                        {% endif %}
                    </td>
                    <td>{{ account.usage_count or 0 }}</td>
                    <td>{{ account.last_used_at.strftime('%Y-%m-%d %H:%M') if account.last_used_at else '婵炲濮寸€涒晛锕㈤鐔稿閻犳亽鍔嶉弳? }}</td>
                    <td>{{ account.created_at.strftime('%Y-%m-%d %H:%M') if account.created_at else '' }}</td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="setCurrent({{ loop.index0 }})">闁荤姳绀佽ぐ鐐垫嫻閻旀眹浜归柟鎯у暱椤?/button>
                        {% if account.is_flagged %}
                            <button class="btn btn-success btn-sm" onclick="unflagAccount({{ account.id }})">闂佸憡鐟﹂悧妤冪矓閻戣棄鍐€闁搞儺浜堕崬?/button>
                        {% else %}
                            <button class="btn btn-danger btn-sm" onclick="flagAccount({{ account.id }})">闂佸搫绉村ú鈺咁敊?/button>
                        {% endif %}
                        <button class="btn btn-secondary btn-sm" onclick="editAccount({{ account.id }})">缂傚倸鍊归悧鐐垫?/button>
                        <button class="btn btn-info btn-sm" onclick="githubLogin('{{ account.email }}', '{{ account.github_password or account.password }}', '{{ account.tfa_secret or '' }}')">GitHub闂佽皫鍡╁殭缂?/button>
                        <div class="copy-dropdown">
                            <button class="btn btn-primary btn-sm">婵犮垼娉涚粔鎾春?闂?/button>
                            <div class="copy-dropdown-content">
                                <a href="#" onclick="copyToClipboard('{{ account.email }}', '闁荤姵鍔х粻鎴ｃ亹?); return false;">婵犮垼娉涚粔鎾春濡ゅ啯瀚婚柨鏇楀亾鐟?/a>
                                <a href="#" onclick="copyToClipboard('{{ account.password }}', '闁诲酣娼уΛ娑㈡偉?); return false;">婵犮垼娉涚粔鎾春濡ゅ啠鍋撻棃娑欘棤闁?/a>
                                {% if account.tfa_secret %}
                                <a href="#" onclick="copyToClipboard('{{ account.tfa_secret }}', '2FA闁诲酣娼уΛ婵嬪箰?); return false;">婵犮垼娉涚粔鎾春?FA</a>
                                {% endif %}
                                <a href="#" onclick="copyAccountInfo({{ account.id }}); return false;">婵犮垼娉涚粔鎾春濡ゅ懎绀傞柕濞炬櫅閸?/a>
                            </div>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- 濠电儑缍€椤曆勬叏閻愬灚瀚婚柨鏃囨閻撴洘淇婇妤€澧查柍褜鍏涢悞锕傘€?-->
    <div id="addModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('addModal')">&times;</span>
            <h2>濠电儑缍€椤曆勬叏閻愮儤鐒芥い鏃傝檸閸炴悂鎮归幇鍫曟闁?/h2>
            <form id="addForm">
                <div class="form-group">
                    <label>闂備緡鍙庨崰姘额敊閸儱鎹堕柡澶嬪缁?</label>
                    <input type="email" name="email" required>
                </div>
                <div class="form-group">
                    <label>闁诲酣娼уΛ娑㈡偉?</label>
                    <input type="password" name="password" required>
                </div>
                <div class="form-group">
                    <label>Client ID:</label>
                    <input type="text" name="client_id" required>
                </div>
                <div class="form-group">
                    <label>闁荤姳绀佸鈥澄涢懜鐢殿浄闁靛牆娲ら·?</label>
                    <textarea name="access_token" rows="3"></textarea>
                </div>
                <div class="form-group">
                    <label>2FA闁诲酣娼уΛ婵嬪箰?</label>
                    <input type="text" name="tfa_secret">
                </div>
                <div class="form-group">
                    <label>闂佸湱绮崝鎺旀閻㈢鐤?</label>
                    <select name="provider">
                        <option value="outlook">Outlook</option>
                        <option value="hotmail">Hotmail</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">濠电儑缍€椤曆勬叏閻愬灚瀚婚柨鏃囨閻?/button>
            </form>
        </div>
    </div>

    <!-- 缂傚倸鍊归悧鐐垫椤愩倖瀚婚柨鏃囨閻撴洘淇婇妤€澧查柍褜鍏涢悞锕傘€?-->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('editModal')">&times;</span>
            <h2>缂傚倸鍊归悧鐐垫椤愶附鐒芥い鏃傝檸閸炴悂鎮归幇鍫曟闁?/h2>
            <form id="editForm">
                <input type="hidden" id="editAccountId" name="account_id">
                <div class="form-group">
                    <label>闂備緡鍙庨崰姘额敊閸儱鎹堕柡澶嬪缁?</label>
                    <input type="email" id="editEmail" name="email" required>
                </div>
                <div class="form-group">
                    <label>闁诲酣娼уΛ娑㈡偉?</label>
                    <input type="password" id="editPassword" name="password" required>
                </div>
                <div class="form-group">
                    <label>Client ID:</label>
                    <input type="text" id="editClientId" name="client_id" required>
                </div>
                <div class="form-group">
                    <label>闁荤姳绀佸鈥澄涢懜鐢殿浄闁靛牆娲ら·?</label>
                    <textarea id="editAccessToken" name="access_token" rows="3"></textarea>
                </div>
                <div class="form-group">
                    <label>2FA闁诲酣娼уΛ婵嬪箰?</label>
                    <input type="text" id="editTfaSecret" name="tfa_secret">
                </div>
                <div class="form-group">
                    <label>闂佸湱绮崝鎺旀閻㈢鐤?</label>
                    <select id="editProvider" name="provider">
                        <option value="outlook">Outlook</option>
                        <option value="hotmail">Hotmail</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">婵烇絽娲︾换鍌炴偤閵婏妇鈹嶆い鏃囧Г閺?/button>
            </form>
        </div>
    </div>

    <script>
        // 闂佺懓鍚嬬划搴ㄥ磼閵娾晛妞界€光偓閳ь剟鎮洪锔界劵濠㈣泛锕ら～鐘绘煠?        function filterTable() {
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

                // 闂佸吋鍎抽崲鑼躲亹閸ヮ剙瑙﹂柛鏇ㄥ亜閻忔瑩鏌ｉ妸銉ヮ仼闁?                const email = cells[1] ? (cells[1].textContent || cells[1].innerText).toLowerCase() : '';
                const provider = cells[2] ? (cells[2].textContent || cells[2].innerText).toLowerCase() : '';
                const hasTfa = cells[3] ? (cells[3].textContent || cells[3].innerText).includes('2FA') : false;
                const isFlagged = row.classList.contains('flagged-row');
                const createdAt = cells[7] ? (cells[7].textContent || cells[7].innerText).trim() : '';

                // 闁圭厧鐡ㄥ濠氬极閵堝洨椹虫繛鎴旀噰閸嬫挻寰勭€ｎ偉鎷繛?                let showRow = true;

                // 闂佺懓鍚嬬划搴ㄥ磼閵娧呴┏婵炴垟鎳囬崑?                if (searchTerm && email.indexOf(searchTerm) === -1) {
                    showRow = false;
                }

                // 闂佸湱绮崝鎺旀閻㈢鐤柛鈩冪懅閹斤綁姊?                if (providerValue && provider.indexOf(providerValue) === -1) {
                    showRow = false;
                }

                // 2FA缂備焦绋掗惄顖炲焵?                if (tfaValue === 'yes' && !hasTfa) {
                    showRow = false;
                } else if (tfaValue === 'no' && hasTfa) {
                    showRow = false;
                }

                // 闂佸搫绉村ú鈺咁敊閸ヮ剚鍋愰柤鍝ヮ暯閸嬫挻鎷呴搹瑙勬噣闂?                if (flagValue === 'flagged' && !isFlagged) {
                    showRow = false;
                } else if (flagValue === 'normal' && isFlagged) {
                    showRow = false;
                }

                // 闂佸搫鍟悥鐓幬涚捄銊ч┏婵炴垟鎳囬崑鎾村緞濞戞氨顦╅梺绯曟櫈濡椼劎鑺遍鍕婵炴垶顭囩槐锕傛煛閸愩劎鍩ｆ俊顐㈡健閺?                if (timeValue && createdAt) {
                    const now = new Date();
                    try {
                        const createdDate = new Date(createdAt.replace(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})/, '$1/$2/$3 $4:$5'));

                        if (timeValue === 'week') {
                            // 婵炴垶鎸撮崑鎾绘煕濞戞牕濡哄ù婊勫笚缁?                            const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                            if (createdDate > weekAgo) {
                                showRow = false;
                            }
                        } else if (timeValue === 'month') {
                            // 婵炴垶鎸撮崑鎾斥槈閹垮啩绨兼繝鈧埀顒€霉閻橆喖鍔欑紒?                            const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                            if (createdDate > monthAgo) {
                                showRow = false;
                            }
                        }
                    } catch (e) {
                        // 闁荤喐鐟辩徊楣冩倵閼恒儱绶為弶鍫亯琚濋梺鎸庣☉婵傛梻鎹㈠璺虹濞达綀顫夐埢鏃傜磼閳?                        console.warn('闂佸搫鍟悥鐓幬涚捄銊﹀枂闁挎繂妫涢埀顒冨Г瀵板嫭娼忛銉?', createdAt, e);
                    }
                } else if (timeValue === 'never') {
                    // 婵炲濮寸€涒晛锕㈤鐔稿閻犳亽鍔嶉弳?- 濠碘槅鍋€閸嬫捇鏌＄仦璇插姕婵炴挸鐖煎畷銉︽償濠靛棌鏋忛梺娲绘娇閸斿秴顪冮崒鐐粹拻?                    const lastUsed = cells[6] ? (cells[6].textContent || cells[6].innerText).trim() : '';
                    if (lastUsed !== '婵炲濮寸€涒晛锕㈤鐔稿閻犳亽鍔嶉弳?) {
                        showRow = false;
                    }
                }

                row.style.display = showRow ? '' : 'none';
            }
        }

        // 濠电偞鎸搁幊妯衡枍鎼淬劌绠ラ柍褜鍓熷鍨緞瀹€鈧幗锝夋⒑?        function clearFilters() {
            document.getElementById('searchInput').value = '';
            document.getElementById('providerFilter').value = '';
            document.getElementById('tfaFilter').value = '';
            document.getElementById('flagFilter').value = '';
            document.getElementById('timeFilter').value = '';
            filterTable();
        }

        // 婵犮垼娉涚粔鎾春濡ゅ懎绀嗛柡澶婄仢椤ュ懘鎮归幇顒傛憼婵?        function copyToClipboard(text, type) {
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(() => {
                    showToast(`${type}閻庣懓鎲¤ぐ鍐囬弻銉ョ閻犲搫鎼悡鍌炴煕閹垮啩娴烽柛鎺撶洴瀵墎缂?;
                }).catch(err => {
                    console.error('婵犮垼娉涚粔鎾春濡や礁绶為弶鍫亯琚?', err);
                    fallbackCopyTextToClipboard(text, type);
                });
            } else {
                fallbackCopyTextToClipboard(text, type);
            }
        }

        // 婵犮垼娉涘ú銊╁极閵堝棗绶炵€广儱鎳庨悡鎴︽煛閸屾繍娼愮痪?        function fallbackCopyTextToClipboard(text, type) {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.top = "0";
            textArea.style.left = "0";
            textArea.style.position = "fixed";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    showToast(`${type}閻庣懓鎲¤ぐ鍐囬弻銉ョ閻犲搫鎼悡鍌炴煕閹垮啩娴烽柛鎺撶洴瀵墎缂?;
                } else {
                    showToast(`婵犮垼娉涚粔鎾春?{type}婵犮垺鍎肩划鍓ф喆椤?;
                }
            } catch (err) {
                console.error('婵犮垼娉涚粔鎾春濡や礁绶為弶鍫亯琚?', err);
                showToast(`婵犮垼娉涚粔鎾春?{type}婵犮垺鍎肩划鍓ф喆椤?;
            }

            document.body.removeChild(textArea);
        }

        // 婵犮垼娉涚粔鎾春濡ゅ啯瀚婚柨鏃囨閻撴洟鎮楅悷鐗堟拱闁哄棴绲剧粚閬嶅焺閸愌呯
        function copyAccountInfo(accountId) {
            fetch(`/get_account/${accountId}`)
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        const account = result.data;
                        let info = `闂備緡鍙庨崰姘额敊? ${account.email}\n`;
                        info += `闁诲酣娼уΛ娑㈡偉? ${account.password}\n`;
                        info += `Client ID: ${account.client_id}\n`;
                        if (account.access_token) {
                            info += `闁荤姳绀佸鈥澄涢懜鐢殿浄闁靛牆娲ら·? ${account.access_token}\n`;
                        }
                        if (account.tfa_secret) {
                            info += `2FA闁诲酣娼уΛ婵嬪箰? ${account.tfa_secret}\n`;
                        }
                        info += `闂佸湱绮崝鎺旀閻㈢鐤? ${account.provider}`;

                        copyToClipboard(info, '闁荤姵鍔ч梽鍕春濞戞埃鍋撻悷鐗堟拱闁哄棴绲剧粚閬嶅焺閸愌呯');
                    } else {
                        showToast('闂佸吋鍎抽崲鑼躲亹閸モ晜瀚婚柨鏃囨閻撴洖菐閸ワ絽澧插ù鐓庢噺瀵板嫭娼忛銉?);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('闂佸吋鍎抽崲鑼躲亹閸モ晜瀚婚柨鏃囨閻撴洖菐閸ワ絽澧插ù鐓庢噺瀵板嫭娼忛銉?);
                });
        }

        // 闂佸搫瀚晶浠嬪Φ濮樿泛绠甸柟閭﹀枔娴犳稒绻涢幋婵堝濞?        function showToast(message) {
            // 闂佸憡甯楃粙鎴犵磽閹捐绠甸柟閭﹀枔娴犳盯鏌涜箛鎾虫殶缂佲偓?            const toast = document.createElement('div');
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: #28a745;
                color: white;
                padding: 12px 20px;
                border-radius: 4px;
                z-index: 10000;
                font-size: 14px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            `;

            document.body.appendChild(toast);

            // 3缂備礁顦扮敮鎺楀箖濡ゅ懏鍤婃い蹇撳琚熺紓浣割槸椤嘲鈻?            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 3000);
        }
        
        // 濠碘槅鍨崜婵嬪焵椤戣法鍔嶆い銏狀儔楠炴帟顦查柛?        function showAddModal() {
            document.getElementById('addModal').style.display = 'block';
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        // 闁荤姳绀佹晶浠嬫偪閸℃哎浜归柟鎯у暱椤ゅ懘鎮归幇鍫曟闁?        function setCurrent(index) {
            fetch('/set_current', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({index: index})
            }).then(() => location.reload());
        }
        
        // 闂佸搫绉村ú鈺咁敊閸モ晜瀚婚柨鏃囨閻?
        function flagAccount(accountId) {
            const reason = prompt('闁荤姴娲ㄩ弻澶屾椤撱垹绀傞柕澶涘閸ㄥジ鎮规担瑙勭凡閻㈩垼鍋婂畷?', '闂傚倸鍋嗛崳锝夈€傞悾灞惧闁挎棁妫勯悡?);
            if (reason) {
                fetch('/flag_account', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({account_id: accountId, reason: reason})
                }).then(() => location.reload());
            }
        }
        
        // 闂佸憡鐟﹂悧妤冪矓閻戣棄鍐€闁搞儺浜堕崬?
        function unflagAccount(accountId) {
            fetch('/unflag_account', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({account_id: accountId})
            }).then(() => location.reload());
        }
        
        // 缂傚倸鍊归悧鐐垫椤愩倖瀚婚柨鏃囨閻?
        function editAccount(accountId) {
            // 闂佸吋鍎抽崲鑼躲亹閸モ晜瀚婚柨鏃囨閻撴洖菐閸ワ絽澧插ù?            fetch(`/get_account/${accountId}`)
                .then(response => response.json())
                .then(account => {
                    if (account.success) {
                        const data = account.data;
                        document.getElementById('editAccountId').value = data.id;
                        document.getElementById('editEmail').value = data.email;
                        document.getElementById('editPassword').value = data.password;
                        document.getElementById('editClientId').value = data.client_id;
                        document.getElementById('editAccessToken').value = data.access_token || '';
                        document.getElementById('editTfaSecret').value = data.tfa_secret || '';
                        document.getElementById('editProvider').value = data.provider;

                        document.getElementById('editModal').style.display = 'block';
                    } else {
                        alert('闂佸吋鍎抽崲鑼躲亹閸モ晜瀚婚柨鏃囨閻撴洖菐閸ワ絽澧插ù鐓庢噺瀵板嫭娼忛銉?);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('闂佸吋鍎抽崲鑼躲亹閸モ晜瀚婚柨鏃囨閻撴洖菐閸ワ絽澧插ù鐓庢噺瀵板嫭娼忛銉?);
                });
        }

        // 濠电儑缍€椤曆勬叏閻愬灚瀚婚柨鏃囨閻撴洟鎮跺☉鏍у鐎规洜鍠栭獮鎾诲箛椤忓懎鏀?
        document.getElementById('addForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            fetch('/add_account', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(response => {
                if (response.ok) {
                    closeModal('addModal');
                    location.reload();
                } else {
                    alert('濠电儑缍€椤曆勬叏閻愭潙绶為弶鍫亯琚?);
                }
            });
        });

        // 缂傚倸鍊归悧鐐垫椤愩倖瀚婚柨鏃囨閻撴洟鎮跺☉鏍у鐎规洜鍠栭獮鎾诲箛椤忓懎鏀?
        document.getElementById('editForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            fetch('/edit_account', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(response => {
                if (response.ok) {
                    closeModal('editModal');
                    location.reload();
                } else {
                    alert('缂傚倸鍊归悧鐐垫椤愶絽绶為弶鍫亯琚?);
                }
            });
        });

        // GitHub闂佽皫鍡╁殭缂傚秴绉瑰畷娆撴嚍閵夛附顔?
        function githubLogin(username, password, tfaSecret) {
            if (!username || !password) {
                showToast('闂佹椿娼块崝宥夊春濞戙垹瑙︾€广儱鎳忕€氭煡鎮楅棃娑欘棤闁绘牗绮嶇粙澶婎吋閸繂骞嬫繛鎴炴崄濞咃綁鍩?, 'error');
                return;
            }

            // 闂佸搫瀚晶浠嬪Φ濮樿泛绀夐柣妯煎劋缁佷即鏌ｅΟ鍨厫闁?            const button = event.target;
            const originalText = button.textContent;
            button.textContent = '闂佽皫鍡╁殭缂傚秴绉电粙?..';
            button.disabled = true;

            // 闁荤姴顑呴崯浼村极椤ョ挶tHub闂佽皫鍡╁殭缂傚秴浼疨I
            fetch('/api/github/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: username,
                    password: password,
                    tfa_secret: tfaSecret || null,
                    headless: false  // 闂佸搫瀚晶浠嬪Φ濮橆優纭呯疀濮樺吋缍岄梺闈╃祷閸斿酣鎮伴妷鈺佺煑?                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('GitHub闂佽皫鍡╁殭缂傚秴绉归獮瀣箛椤掆偓椤娀鏌ㄥ☉妤冨妽缂佷浇宕甸幉鎾醇濠靛洨褰滈悗鍦焾瀵埖鏅堕敃鈧锝夊焵?, 'success');
                } else {
                    showToast('GitHub闂佽皫鍡╁殭缂傚秴绉靛鍕綇椤愩儛? ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('GitHub闂佽皫鍡╁殭缂傚秴绉归弻銊モ枎閹烘繂娈?', error);
                showToast('GitHub闂佽皫鍡╁殭缂傚秴绉堕幏鐘绘煥鐎ｎ剚鍕炬繝銏″劶缁墽鎲?, 'error');
            })
            .finally(() => {
                // 闂佽鍘归崹褰捤囬弻銉ョ濠㈣埖鍔栫亸锕傛煟濡灝鐓愰柍?                button.textContent = originalText;
                button.disabled = false;
            });
        }

        // 闂佽　鍋撶痪顓炴噽缁犲鏌ｉ妸銉ヮ仾鐟滈鑳剁划鍫ユ倻濡す銉╂煙椤撗冪仩闁搞倝浜跺顐ゆ暜椤斿墽顦梺琛″亾妞ゆ牗绋戦惁顔尖槈閹惧磭孝闁诡喗鎸鹃悮鍓ф嫚閼碱兘鍋?        function showToast(message, type = 'success') {
            // 闂佸憡甯楃粙鎴犵磽閹捐绠甸柟閭﹀枔娴犳盯鏌涜箛鎾虫殶缂佲偓?            const toast = document.createElement('div');
            toast.textContent = message;

            let backgroundColor = '#28a745'; // 婵帗绋掗…鍫ヮ敇婵犳艾绠ｉ柟閭﹀墮椤姷绱撴担钘夊姷濠?            if (type === 'error') {
                backgroundColor = '#dc3545'; // 闂備焦瀵ч悷銊╊敋閵堝洨妫柕蹇ョ到椤?
            } else if (type === 'warning') {
                backgroundColor = '#ffc107'; // 闁荤姭鍋撻柨鏇楀亾闁规祴鍓濋—鈧柛鏇ㄥ枛椤?
            } else if (type === 'info') {
                backgroundColor = '#17a2b8'; // 婵烇絽娲犻崜婵囧閸涘瓨瀚呮繝闈涳工椤?
            }

            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: ${backgroundColor};
                color: white;
                padding: 12px 20px;
                border-radius: 4px;
                z-index: 10000;
                font-size: 14px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                max-width: 300px;
                word-wrap: break-word;
            `;

            document.body.appendChild(toast);

            // 3缂備礁顦扮敮鎺楀箖濡ゅ懏鍤婃い蹇撳琚熺紓浣割槸椤嘲鈻?            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 5000); // 閻庣偣鍊曢悥濂稿汲闁秴绀?缂備礁顦扮敮顏嗘濠靛牏纾兼繛鍡樺灦閺嗗繘鏌熼幘顔芥暠婵炲弶瀵у鍕潩椤撶噥妲梻鍌氬€归幐鍐参ｉ崟顓熷珰?        }

        // 闂佺粯鍔楅幊鎾诲吹椤斿槈鐔煎焺閸愶絽浜惧ù锝堫嚃閺€鍗烆熆閼哥數澧甸柛搴㈡尦瀹曟骞庨懞銉川
        window.onclick = function(event) {
            const modals = document.getElementsByClassName('modal');
            for (let modal of modals) {
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            }
        }
    </script>
</body>
</html>
"""

# 闂佺粯绮犻崹浼淬€傞妸鈺佺煑婵せ鍋撻柛锝嗘そ閺屽﹤顓奸崶鈺傜€俊鐐€楅弫璇差焽閺夎鐔煎焺閸愨晝鍑?
ENV_CONFIG_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>闂佺粯绮犻崹浼淬€傞妸鈺佺煑婵せ鍋撻柛锝嗘そ閺屽﹤顓奸崶鈺傜€?- Navie 闂備緡鍙庨崰姘额敊閸垻涓嶉柨娑樺閸婄偤鏌?/title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .nav-buttons { margin-bottom: 20px; text-align: center; }
        .btn { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-secondary { background-color: #6c757d; color: white; }
        .btn-success { background-color: #28a745; color: white; }
        .btn:hover { opacity: 0.8; }
        .category-section { margin-bottom: 30px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
        .category-header { background-color: #f8f9fa; padding: 15px; font-weight: bold; font-size: 18px; border-bottom: 1px solid #ddd; }
        .config-item { padding: 15px; border-bottom: 1px solid #eee; }
        .config-item:last-child { border-bottom: none; }
        .config-label { font-weight: bold; margin-bottom: 5px; }
        .config-description { color: #666; font-size: 14px; margin-bottom: 10px; }
        .config-input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 5px; }
        .config-input[type="password"] { font-family: monospace; }
        .config-help { color: #888; font-size: 12px; }
        .required { color: #dc3545; }
        .sensitive { background-color: #fff3cd; }
        .toast { position: fixed; top: 20px; right: 20px; background-color: #28a745; color: white; padding: 12px 20px; border-radius: 4px; z-index: 10000; display: none; }
        .loading { opacity: 0.6; pointer-events: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>闂佽櫕瀵ч悷杈╃箔?闂佺粯绮犻崹浼淬€傞妸鈺佺煑婵せ鍋撻柛锝嗘そ閺屽﹤顓奸崶鈺傜€?/h1>

        <div class="nav-buttons">
            <button class="btn btn-secondary" onclick="window.close()">闂?闁哄鏅滈弻銊ッ洪弽銊р枖濠电姵鍝庨埀?/button>
            <button class="btn btn-success" onclick="saveAllConfig()">濡絽鍟畷?婵烇絽娲︾换鍌炴偤閵娾晛绠ラ柍褜鍓熷鍨緞閹邦剙璧嬬紓?/button>
            <button class="btn btn-primary" onclick="loadConfig()">濡絽鍟弫?闂備焦褰冪粔鐢稿蓟婵犲洤绀夐柣妯煎劋缁?/button>
        </div>

        <div id="configContainer">
            <!-- 闂備焦婢樼粔鍫曟偪閸℃ǜ浜滈柣鐔稿濞堟椽姊洪锝勪孩缂佽鍎慳vaScript闂佸憡鏌ｉ崝宥夊焵椤戣法顦﹀┑顔惧仦濞?-->
        </div>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        let configTemplates = [];
        let configValues = {};

        // 婵＄偑鍊楅弫璇差焽娴兼潙绀夐柣妯煎劋缁佷即鏌￠崘顓熺【闁搞劌鐏氶幈銊р偓锝庝簻椤?
        document.addEventListener('DOMContentLoaded', function() {
            loadConfig();
        });

        // 闂佸憡姊绘慨鎯归崶顒佺厐鐎广儱娲ㄩ弸?
        async function loadConfig() {
            try {
                document.body.classList.add('loading');

                // 闂佸吋鍎抽崲鑼躲亹閸ヮ灛鐔煎焺閸愨晝鍑￠梺鍛婄矊閼活垳绱炵€ｎ喖绀堢€广儱鎳夐崑?                const [templatesResponse, valuesResponse] = await Promise.all([
                    fetch('/api/env_config/templates'),
                    fetch('/api/env_config/values')
                ]);

                const templatesData = await templatesResponse.json();
                const valuesData = await valuesResponse.json();

                if (templatesData.success) {
                    configTemplates = templatesData.data;
                }

                if (valuesData.success) {
                    configValues = valuesData.data;
                }

                renderConfig();
                showToast('闂備焦婢樼粔鍫曟偪閸℃稑绀夐柣妯煎劋缁佷即鏌熺€涙ê濮囧┑?);

            } catch (error) {
                console.error('闂佸憡姊绘慨鎯归崶顒佺厐鐎广儱娲ㄩ弸鍌氼熆閹壆绨块悷?', error);
                showToast('闂佸憡姊绘慨鎯归崶顒佺厐鐎广儱娲ㄩ弸鍌氼熆閹壆绨块悷?, 'error');
            } finally {
                document.body.classList.remove('loading');
            }
        }

        // 濠电偞鎸稿鍫曟偂鐎ｎ喗鐓€鐎广儱娲ㄩ弸鍌炴煟閿濆懐鐒告繛?        function renderConfig() {
            const container = document.getElementById('configContainer');
            const categories = {};

            // 闂佸湱顭堥ˇ顖炲垂鎼达絿灏甸柤濮愬€楅惌瀣磽娴ｅ憡鍠橀柛妯稿€楃槐鏃堫敋閳ь剟濡?            configTemplates.forEach(template => {
                if (!categories[template.category]) {
                    categories[template.category] = [];
                }
                categories[template.category].push(template);
            });

            // 闂佸憡甯掑Λ娑氭偖椤愶箑瑙︾€广儱娉﹂悙鍝勫強闁绘灏欏▓?
            const categoryNames = {
                'captcha': '濡絽鍟弫?婵°倗濮撮惌渚€鎯佹径鎰剺濞达綀顫夌粻娑㈡煕?,
                'browser': '濡絽鍟?濠电偞娼欑换妤咃綖瀹ュ闂柕濞炬櫅鐢磭绱?,
                'username': '濡絽鍟崳?闂佹椿娼块崝宥夊春濞戙垹瑙︾€广儱娲﹂弲鎼佹煙?,
                'email_provider': '濡絽鍟幉?闂備緡鍙庨崰姘额敊閸儱瀚夌€广儱鎳庨～銈夋煕?,
                'augment': '濡絽鍟粻?Augment闂佸搫鐗嗙粔瀛樻叏?,
                'payment': '濡絽鍟亸?闂佽　鍋撴い鏍ㄧ懅鐢稑菐閸ワ絽澧插ù?,
                'proxy': '濡絽鍟弲?婵炲濯寸徊鍧楀箖婵犲洦鐓€鐎广儱娲ㄩ弸?
            };

            let html = '';

            Object.keys(categories).forEach(category => {
                const categoryName = categoryNames[category] || category;
                html += `<div class="category-section">`;
                html += `<div class="category-header">${categoryName}</div>`;

                categories[category].forEach(template => {
                    const currentValue = configValues[template.config_key] || template.default_value || '';
                    const isRequired = template.is_required ? '<span class="required">*</span>' : '';
                    const isSensitive = template.is_sensitive ? 'sensitive' : '';
                    const inputType = template.is_sensitive ? 'password' :
                                    template.data_type === 'boolean' ? 'checkbox' : 'text';

                    html += `<div class="config-item ${isSensitive}">`;
                    html += `<div class="config-label">${template.display_name} ${isRequired}</div>`;
                    if (template.description) {
                        html += `<div class="config-description">${template.description}</div>`;
                    }

                    if (template.data_type === 'boolean') {
                        const checked = currentValue === 'true' ? 'checked' : '';
                        html += `<input type="checkbox" id="${template.config_key}" ${checked} onchange="updateConfigValue('${template.config_key}', this.checked)">`;
                    } else {
                        html += `<input type="${inputType}" class="config-input" id="${template.config_key}" value="${currentValue}" placeholder="${template.default_value || ''}" onchange="updateConfigValue('${template.config_key}', this.value)">`;
                    }

                    if (template.help_text) {
                        html += `<div class="config-help">${template.help_text}</div>`;
                    }
                    html += `</div>`;
                });

                html += `</div>`;
            });

            container.innerHTML = html;
        }

        // 闂佸搫娲ら悺銊╁蓟婵犲洦鐓€鐎广儱娲ㄩ弸鍌炴煕?        function updateConfigValue(key, value) {
            // 缂佺虎鍙庨崰鏇犳崲濮樿鲸鏆滈柛鎰╁妿濮ｆ粓鏌涙繝鍛棈婵炴潙妫濋獮鎴︼綖椤擄紕顦伴柣搴㈢⊕椤ㄥ牓顢栨担鍦枖闁圭粯甯為幗鐘绘煕鐏炶濡奸柛鈺佺焸瀵偊鎮ч崼婵堛偊闁?            if (typeof value === 'boolean') {
                configValues[key] = value.toString();
            } else {
                configValues[key] = value;
            }
        }

        // 婵烇絽娲︾换鍌炴偤閵娾晛绠ラ柍褜鍓熷鍨緞閹邦剙璧嬬紓?        async function saveAllConfig() {
            try {
                document.body.classList.add('loading');

                const response = await fetch('/api/env_config/batch_update', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({env_vars: configValues})
                });

                const result = await response.json();

                if (result.success) {
                    showToast('闂備焦婢樼粔鍫曟偪閸℃鈹嶆繝闈涙閹界娀鏌熺€涙ê濮囧┑?);
                } else {
                    showToast('闂備焦婢樼粔鍫曟偪閸℃鈹嶆繝闈涙閹界姴顭块幆鎵翱閻?, 'error');
                }

            } catch (error) {
                console.error('婵烇絽娲︾换鍌炴偤閵娾晜鐓€鐎广儱娲ㄩ弸鍌氼熆閹壆绨块悷?', error);
                showToast('婵烇絽娲︾换鍌炴偤閵娾晜鐓€鐎广儱娲ㄩ弸鍌氼熆閹壆绨块悷?, 'error');
            } finally {
                document.body.classList.remove('loading');
            }
        }

        // 闂佸搫瀚晶浠嬪Φ濮樿泛绠甸柟閭﹀枔娴犳稒绻涢幋婵堝濞?        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.backgroundColor = type === 'error' ? '#dc3545' : '#28a745';
            toast.style.display = 'block';

            setTimeout(() => {
                toast.style.display = 'none';
            }, 3000);
        }
    </script>
</body>
</html>
"""

# 闂備緡鍙庨崰姘额敊閸儱鐭楅柡宓啫鈻忔俊鐐€楅弫璇差焽閺夎鐔煎焺閸愨晝鍑?
EMAIL_FETCH_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>闂備緡鍙庨崰姘额敊閸儱鐭楅柡宓啫鈻?- Navie 闂備緡鍙庨崰姘额敊閸垻涓嶉柨娑樺閸婄偤鏌?/title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .nav-buttons { margin-bottom: 20px; text-align: center; }
        .btn { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-secondary { background-color: #6c757d; color: white; }
        .btn-success { background-color: #28a745; color: white; }
        .btn-warning { background-color: #ffc107; color: black; }
        .btn:hover { opacity: 0.8; }
        .info-card { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .info-item { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .info-label { font-weight: bold; }
        .info-value { color: #007bff; }
        .fetch-form { background-color: #fff; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .result-area { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin-top: 20px; display: none; }
        .success-list { color: #28a745; }
        .error-list { color: #dc3545; }
        .loading { opacity: 0.6; pointer-events: none; }
        .toast { position: fixed; top: 20px; right: 20px; background-color: #28a745; color: white; padding: 12px 20px; border-radius: 4px; z-index: 10000; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>濡絽鍟幉?闂備緡鍙庨崰姘额敊閸儱鐭楅柡宓啫鈻忛梺鍝勭墕缁夊瓨鎱?/h1>

        <div class="nav-buttons">
            <button class="btn btn-secondary" onclick="window.close()">闂?闁哄鏅滈弻銊ッ洪弽銊р枖濠电姵鍝庨埀?/button>
            <button class="btn btn-warning" onclick="refreshInfo()">濡絽鍟弫?闂佸憡甯￠弨閬嶅蓟婵犲啰鈹嶉柍鈺佸暕缁?/button>
        </div>

        <!-- 闂佸搫鐗嗙粔瀛樻叏閻斿摜鈹嶉柍鈺佸暕缁辨牠鏌涘Δ瀣？濠?-->
        <div class="info-card">
            <h3>濡絽鍟幆?闂傚倸鍋嗘禍顏堝磻閺嶎偆涓嶉弶鍫涘妽缁犳盯鏌涢弮鎾剁？濠殿喗鎮傞獮鈧?/h3>
            <div class="info-item">
                <span class="info-label">閻熸粎澧楅幐鍛婃櫠閻樿櫕濯存繛鍡樻惄閺?</span>
                <span class="info-value" id="balance">闂佸憡姊绘慨鎯归崶銊р枖?..</span>
            </div>
            <div class="info-item">
                <span class="info-label">闁圭厧鐡ㄩ幐鎼佹偤閵娾晜鍋愰柤鍝ヮ暯閸?</span>
                <span class="info-value" id="stock">闂佸憡姊绘慨鎯归崶銊р枖?..</span>
            </div>
            <div class="info-item">
                <span class="info-label">闂佸搫鐗嗙粔瀛樻叏閻斿吋鍋愰柤鍝ヮ暯閸?</span>
                <span class="info-value" id="status">濠碘槅鍋€閸嬫捇鏌＄仦璇插姍闁?..</span>
            </div>
        </div>

        <!-- 闂佸憡鐟﹂悧鏇°亹鐠恒劍鍋橀柕濞垮劚缁€?-->
        <div class="fetch-form">
            <h3>濡絽鍟粻?闂備緡鍙庨崰姘额敊閸儱鐭楅柡宓啫鈻?/h3>
            <div class="form-group">
                <label>闂備緡鍙庨崰姘额敊閸垻灏甸悹鍥皺閳?</label>
                <select id="emailType">
                    <option value="outlook">Outlook</option>
                    <option value="hotmail">Hotmail</option>
                </select>
            </div>
            <div class="form-group">
                <label>闂佸憡鐟﹂悧鏇°亹閸ф鏋佸ù鍏兼綑濞?</label>
                <input type="number" id="fetchCount" min="1" max="10" value="1" placeholder="闁荤姴娲ㄩ弻澶屾椤撱垹绀傞柕澶堝劚缁插潡鏌涘▎鎾存暠闁哄棛鍠栭弻?>
            </div>
            <button class="btn btn-success" onclick="fetchEmails()" id="fetchBtn">濡絽鍟悾?閻庢鍠掗崑鎾斥攽椤旂⒈鍎忕憸鏉挎喘瀹?/button>
        </div>

        <!-- 缂傚倷鐒﹂幐濠氭倶婢舵劕鍙婇柛鎾椾椒绮甸梺鍛婄墪閹碱偊鎮?-->
        <div class="result-area" id="resultArea">
            <h3>濡絽鍟幆?闂佸憡鐟﹂悧鏇°亹鐠恒劎纾奸柟鎯ь嚟娴?/h3>
            <div id="resultContent"></div>
        </div>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        // 婵＄偑鍊楅弫璇差焽娴兼潙绀夐柣妯煎劋缁佷即鏌￠崘顓熺【闁搞劌鐏氶幈銊р偓锝庝簻椤?
        document.addEventListener('DOMContentLoaded', function() {
            refreshInfo();
        });

        // 闂佸憡甯￠弨閬嶅蓟婵犲洤瀚夌€广儱鎳庨～銈吳庨崶锝呭⒉濞?        async function refreshInfo() {
            try {
                document.body.classList.add('loading');

                // 闂佸吋鍎抽崲鑼躲亹閸ャ劍濯存繛鍡樻惄閺?
                const balanceResponse = await fetch('/api/shan_mail/balance');
                const balanceData = await balanceResponse.json();

                if (balanceData.success) {
                    document.getElementById('balance').textContent = balanceData.balance + ' 婵?;
                    document.getElementById('status').textContent = '濠殿喗绻愮徊浠嬫偉?;
                    document.getElementById('status').style.color = '#28a745';
                } else {
                    document.getElementById('balance').textContent = '闂佸吋鍎抽崲鑼躲亹閸ャ劌绶為弶鍫亯琚?;
                    document.getElementById('status').textContent = balanceData.message || '閻庢鍠栭崐鎼佹偉?;
                    document.getElementById('status').style.color = '#dc3545';
                }

                // 闂佸吋鍎抽崲鑼躲亹閸ャ劍鍎熼柟鎯х－閹?
                const stockResponse = await fetch('/api/shan_mail/stock');
                const stockData = await stockResponse.json();

                if (stockData.success) {
                    const stockText = typeof stockData.stock === 'object' ?
                        JSON.stringify(stockData.stock) : stockData.stock;
                    document.getElementById('stock').textContent = stockText;
                } else {
                    document.getElementById('stock').textContent = '闂佸吋鍎抽崲鑼躲亹閸ャ劌绶為弶鍫亯琚?;
                }

            } catch (error) {
                console.error('闂佸憡甯￠弨閬嶅蓟婵犲啰鈹嶉柍鈺佸暕缁辨牕顭块幆鎵翱閻?', error);
                document.getElementById('balance').textContent = '缂傚倸鍟崹鍦垝閸洘鐓ユ繛鍡樺俯閸?;
                document.getElementById('stock').textContent = '缂傚倸鍟崹鍦垝閸洘鐓ユ繛鍡樺俯閸?;
                document.getElementById('status').textContent = '缂傚倸鍟崹鍦垝閸洘鐓ユ繛鍡樺俯閸?;
                document.getElementById('status').style.color = '#dc3545';
            } finally {
                document.body.classList.remove('loading');
            }
        }

        // 闂佸憡鐟﹂悧鏇°亹閸ф绠肩€广儱瀚粙?
        async function fetchEmails() {
            const emailType = document.getElementById('emailType').value;
            const fetchCount = parseInt(document.getElementById('fetchCount').value);

            if (!fetchCount || fetchCount < 1 || fetchCount > 10) {
                showToast('闁荤姴娲ㄩ弻澶屾椤撱垹绀傞柕澶涢檮缁犳帡鏌℃担鍝ュⅱ婵炲牊鍨垮畷锝夊冀瑜嶆繛鍥煛娴ｅ嘲宓嗛柛?(1-10)', 'error');
                return;
            }

            try {
                document.body.classList.add('loading');
                document.getElementById('fetchBtn').textContent = '闂佸憡鐟﹂悧鏇°亹閹稿海鈻?..';

                const response = await fetch('/api/shan_mail/fetch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        count: fetchCount,
                        email_type: emailType
                    })
                });

                const result = await response.json();

                // 闂佸搫瀚晶浠嬪Φ濮樿京纾奸柟鎯ь嚟娴?
                displayResult(result);

                if (result.success) {
                    showToast(result.message);
                    // 闂佸憡甯￠弨閬嶅蓟婵犲啯濯存繛鍡樻惄閺夊搫菐閸ワ絽澧插ù?                    setTimeout(refreshInfo, 1000);
                } else {
                    showToast(result.message, 'error');
                }

            } catch (error) {
                console.error('闂佸憡鐟﹂悧鏇°亹閹稿骸绶為弶鍫亯琚?', error);
                showToast('闂佸憡鐟﹂悧鏇°亹閸ф绠肩€广儱瀚粙濠傤熆閹壆绨块悷?, 'error');
            } finally {
                document.body.classList.remove('loading');
                document.getElementById('fetchBtn').textContent = '濡絽鍟悾?閻庢鍠掗崑鎾斥攽椤旂⒈鍎忕憸鏉挎喘瀹?;
            }
        }

        // 闂佸搫瀚晶浠嬪Φ濮樿泛鐭楅柡宓啫鈻忕紓鍌欑劍閹稿鎮?        function displayResult(result) {
            const resultArea = document.getElementById('resultArea');
            const resultContent = document.getElementById('resultContent');

            let html = '';

            if (result.success) {
                html += `<div class="success-list">`;
                html += `<h4>闂?闂佸憡鐟﹂悧鏇°亹閸ф绠ｉ柟閭﹀墮椤?/h4>`;
                html += `<p>闁荤姴娲弨閬嶆儑娴兼潙鏋佸ù鍏兼綑濞? ${result.total_requested}</p>`;
                html += `<p>闂佺懓鐡ㄩ崝鏇熸叏濞戞〒搴ｆ嫚閹绘帩娼? ${result.total_added}</p>`;

                if (result.added_accounts && result.added_accounts.length > 0) {
                    html += `<h5>闂佺懓鐡ㄩ崝鏇熸叏濞戞〒搴ｆ嫚閹绘帩娼遍梺姹囧妼鐎氫即宕戦弽顐や笉?</h5>`;
                    html += `<ul>`;
                    result.added_accounts.forEach(email => {
                        html += `<li>${email}</li>`;
                    });
                    html += `</ul>`;
                }

                if (result.failed_accounts && result.failed_accounts.length > 0) {
                    html += `<div class="error-list">`;
                    html += `<h5>婵犮垺鍎肩划鍓ф喆閿曞倹鍎嶉柛鏇ㄥ灠娴犲繒绱?</h5>`;
                    html += `<ul>`;
                    result.failed_accounts.forEach(email => {
                        html += `<li>${email}</li>`;
                    });
                    html += `</ul>`;
                    html += `</div>`;
                }

                html += `</div>`;
            } else {
                html += `<div class="error-list">`;
                html += `<h4>闂?闂佸憡鐟﹂悧鏇°亹閹稿骸绶為弶鍫亯琚?/h4>`;
                html += `<p>${result.message}</p>`;
                html += `</div>`;
            }

            resultContent.innerHTML = html;
            resultArea.style.display = 'block';
        }

        // 闂佸搫瀚晶浠嬪Φ濮樿泛绠甸柟閭﹀枔娴犳稒绻涢幋婵堝濞?        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.backgroundColor = type === 'error' ? '#dc3545' : '#28a745';
            toast.style.display = 'block';

            setTimeout(() => {
                toast.style.display = 'none';
            }, 3000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """婵炴垶鎸搁…鐑藉Υ婢舵劖顥?""
    async def get_data():
        conn = await get_db_connection()
        try:
            # 闂佸吋鍎抽崲鑼躲亹閸ヮ剙绠ラ柍褜鍓熷鍨緞鎼粹槅妲遍梺?            accounts = await conn.fetch("""
                SELECT id, email, password, github_password, client_id, access_token, tfa_secret,
                       is_flagged, flag_reason, provider, usage_count, 
                       last_used_at, created_at
                FROM email_accounts 
                WHERE is_active = true
                ORDER BY created_at ASC
            """)
            
            # 闂佸吋鍎抽崲鑼躲亹閸ヮ亗浜归柟鎯у暱椤ゅ懘鎮归幇鍫曟闁糕晜绋撳Σ鎰板閻樼數鈹?
            current_index = await conn.fetchval("""
                SELECT config_value FROM email_config 
                WHERE config_key = 'current_account_index'
            """)
            current_index = int(current_index) if current_index else 0
            
            # 闂佸吋鍎抽崲鑼躲亹閸モ晝纾奸柣鏃€妞块崥鈧繛锝呮礌閸撴繃瀵?            stats = await conn.fetchrow("""
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
    """濠电儑缍€椤曆勬叏閻愬灚瀚婚柨鏃囨閻?""
    data = request.json
    
    async def add_account_async():
        conn = await get_db_connection()
        try:
            await conn.execute("""
                INSERT INTO email_accounts (email, password, github_password, client_id, access_token, tfa_secret, provider)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (email) DO UPDATE SET
                    password = EXCLUDED.password,
                    github_password = EXCLUDED.github_password,
                    client_id = EXCLUDED.client_id,
                    access_token = EXCLUDED.access_token,
                    tfa_secret = EXCLUDED.tfa_secret,
                    provider = EXCLUDED.provider,
                    updated_at = CURRENT_TIMESTAMP
            """, data['email'], data['password'], data.get('github_password') or None, data['client_id'], 
                 data.get('access_token') or None, data.get('tfa_secret') or None, 
                 data.get('provider', 'outlook'))
            return True
        except Exception as e:
            logger.error(f"濠电儑缍€椤曆勬叏閻愬灚瀚婚柨鏃囨閻撴洖顭块幆鎵翱閻? {e}")
            return False
        finally:
            await conn.close()
    
    success = run_async(add_account_async())
    return jsonify({'success': success})

@app.route('/set_current', methods=['POST'])
def set_current():
    """闁荤姳绀佹晶浠嬫偪閸℃哎浜归柟鎯у暱椤ゅ懘鎮归幇鍫曟闁?""
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
            logger.error(f"闁荤姳绀佹晶浠嬫偪閸℃哎浜归柟鎯у暱椤ゅ懘鎮归幇鍫曟闁糕晜绋掑鍕綇椤愩儛? {e}")
            return False
        finally:
            await conn.close()
    
    success = run_async(set_current_async())
    return jsonify({'success': success})

@app.route('/flag_account', methods=['POST'])
def flag_account():
    """闂佸搫绉村ú鈺咁敊閸モ晜瀚婚柨鏃囨閻?""
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
            logger.error(f"闂佸搫绉村ú鈺咁敊閸モ晜瀚婚柨鏃囨閻撴洖顭块幆鎵翱閻? {e}")
            return False
        finally:
            await conn.close()
    
    success = run_async(flag_account_async())
    return jsonify({'success': success})

@app.route('/unflag_account', methods=['POST'])
def unflag_account():
    """闂佸憡鐟﹂悧妤冪矓閻戣棄鍐€闁搞儺浜堕崬鍫曟偣閹板爼妾柛?""
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
            logger.error(f"闂佸憡鐟﹂悧妤冪矓閻戣棄鍐€闁搞儺浜堕崬鍫曟偣閹板爼妾柛鈺傜⊕瀵板嫭娼忛銉? {e}")
            return False
        finally:
            await conn.close()

    success = run_async(unflag_account_async())
    return jsonify({'success': success})

@app.route('/get_account/<int:account_id>')
def get_account(account_id):
    """闂佸吋鍎抽崲鑼躲亹閸モ晜瀚婚柨鏃囨閻撴洖菐閸ワ絽澧插ù?""
    async def get_account_async():
        conn = await get_db_connection()
        try:
            account = await conn.fetchrow("""
                SELECT id, email, password, github_password, client_id, access_token, tfa_secret, provider
                FROM email_accounts
                WHERE id = $1 AND is_active = true
            """, account_id)

            if account:
                return dict(account)
            else:
                return None
        except Exception as e:
            logger.error(f"闂佸吋鍎抽崲鑼躲亹閸モ晜瀚婚柨鏃囨閻撴洖菐閸ワ絽澧插ù鐓庢噺瀵板嫭娼忛銉? {e}")
            return None
        finally:
            await conn.close()

    account = run_async(get_account_async())
    if account:
        return jsonify({'success': True, 'data': account})
    else:
        return jsonify({'success': False, 'message': '闁荤姵鍔ч梽鍕春濞戞瑧鈻旂€广儱鎳愰幗鐘绘煕?})

@app.route('/edit_account', methods=['POST'])
def edit_account():
    """缂傚倸鍊归悧鐐垫椤愩倖瀚婚柨鏃囨閻?""
    data = request.json

    async def edit_account_async():
        conn = await get_db_connection()
        try:
            await conn.execute("""
                UPDATE email_accounts
                SET email = $2, password = $3, github_password = $4, client_id = $5, access_token = $6,
                    tfa_secret = $7, provider = $8, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, data['account_id'], data['email'], data['password'], data.get('github_password') or None, data['client_id'],
                 data.get('access_token') or None, data.get('tfa_secret') or None,
                 data.get('provider', 'outlook'))
            return True
        except Exception as e:
            logger.error(f"缂傚倸鍊归悧鐐垫椤愩倖瀚婚柨鏃囨閻撴洖顭块幆鎵翱閻? {e}")
            return False
        finally:
            await conn.close()

    success = run_async(edit_account_async())
    return jsonify({'success': success})

@app.route('/env_config')
def env_config():
    """闂佺粯绮犻崹浼淬€傞妸鈺佺煑婵せ鍋撻柛锝嗘そ閺屽﹤顓奸崶鈺傜€俊鐐€楅弫璇差焽?""
    return render_template_string(ENV_CONFIG_TEMPLATE)

@app.route('/api/env_config/templates')
def get_env_config_templates():
    """闂佸吋鍎抽崲鑼躲亹閸ヮ剚鍋濇い鏍ㄥ嚬閺嗘棃鏌涘▎鎰惰€块柛锝呮惈铻ｉ柍鈺佸暞缁?""
    async def get_templates_async():
        conn = await get_db_connection()
        try:
            templates = await conn.fetch("""
                SELECT config_key, display_name, description, category, data_type,
                       default_value, is_required, is_sensitive, help_text
                FROM env_config_templates
                ORDER BY category, config_key
            """)
            return [dict(template) for template in templates]
        except Exception as e:
            logger.error(f"闂佸吋鍎抽崲鑼躲亹閸ヮ剚鍋濇い鏍ㄥ嚬閺嗘棃鏌涘▎鎰惰€块柛锝呮惈铻ｉ柍鈺佸暞缁舵彃顭块幆鎵翱閻? {e}")
            return []
        finally:
            await conn.close()

    templates = run_async(get_templates_async())
    return jsonify({'success': True, 'data': templates})

@app.route('/api/env_config/values')
def get_env_config_values():
    """闂佸吋鍎抽崲鑼躲亹閸ヮ剚鍋濇い鏍ㄥ嚬閺嗘棃鏌涘▎鎰惰€块柛锝夌細閵囨劙骞橀崘宸瀫闂?""
    async def get_values_async():
        conn = await get_db_connection()
        try:
            values = await conn.fetch("""
                SELECT config_key, config_value
                FROM email_config
                WHERE config_type = 'env_var'
            """)
            return {row['config_key']: row['config_value'] for row in values}
        except Exception as e:
            logger.error(f"闂佸吋鍎抽崲鑼躲亹閸ヮ剚鍋濇い鏍ㄥ嚬閺嗘棃鏌涘▎鎰惰€块柛锝嗘そ瀹曟劙鎮℃惔娑楁澀闁? {e}")
            return {}
        finally:
            await conn.close()

    values = run_async(get_values_async())
    return jsonify({'success': True, 'data': values})

@app.route('/api/env_config/update', methods=['POST'])
def update_env_config():
    """闂佸搫娲ら悺銊╁蓟婵犲洦鍋濇い鏍ㄥ嚬閺嗘棃鏌涘▎鎰惰€块柛?""
    data = request.json
    config_key = data.get('config_key')
    config_value = data.get('config_value', '')

    async def update_env_async():
        conn = await get_db_connection()
        try:
            # 缂佺虎鍙庨崰鏇犳崲濮樿泛纾归柤鍦缁侇噣鏌熺拠鈩冪窔閻犳劗鍠撻埀顒佺⊕椤ㄥ牓顢栨担鍦枖閻犲泧鍛槷闂佺粯顨堥幊鎾诲春閸℃稑鍙婃い鏍ㄦ皑椤忔挳鎮樿箛鏃€鐓ラ柍?            if isinstance(config_value, bool):
                config_value_str = str(config_value).lower()
            else:
                config_value_str = str(config_value) if config_value is not None else ''

            await conn.execute("""
                INSERT INTO email_config (config_key, config_value, config_type, category)
                VALUES ($1, $2, 'env_var', 'environment')
                ON CONFLICT (config_key)
                DO UPDATE SET
                    config_value = EXCLUDED.config_value,
                    updated_at = CURRENT_TIMESTAMP
            """, config_key, config_value_str)
            return True
        except Exception as e:
            logger.error(f"闂佸搫娲ら悺銊╁蓟婵犲洦鍋濇い鏍ㄥ嚬閺嗘棃鏌涘▎鎰惰€块柛锝囧劋瀵板嫭娼忛銉? {e}")
            return False
        finally:
            await conn.close()

    success = run_async(update_env_async())
    return jsonify({'success': success})

@app.route('/api/env_config/batch_update', methods=['POST'])
def batch_update_env_config():
    """闂佸綊娼х紞濠囧闯濞差亜鍗抽悗娑櫳戦悡鈧梺缁樼矤閸ㄤ即銆傞妸鈺佺煑婵せ鍋撻柛?""
    data = request.json
    env_vars = data.get('env_vars', {})

    async def batch_update_async():
        conn = await get_db_connection()
        try:
            async with conn.transaction():
                for config_key, config_value in env_vars.items():
                    # 缂佺虎鍙庨崰鏇犳崲濮樿泛绠ラ柍褜鍓熷鍨緞婵炴儳浜惧┑鍌滎焾閸樻挳寮堕悜鍡楀鐎规洖寮剁粙澶愬传閸曨厽鎲荤紓浣诡殣缂傛氨鎲伴崱娑欐櫖鐎光偓閳ь剚绔熼幒妤€绀嗘い鎰剁稻绗戦柣銏╁灠閸燁偊鎯冮悽绋跨９?                    if isinstance(config_value, bool):
                        config_value_str = str(config_value).lower()
                    else:
                        config_value_str = str(config_value) if config_value is not None else ''

                    await conn.execute("""
                        INSERT INTO email_config (config_key, config_value, config_type, category)
                        VALUES ($1, $2, 'env_var', 'environment')
                        ON CONFLICT (config_key)
                        DO UPDATE SET
                            config_value = EXCLUDED.config_value,
                            updated_at = CURRENT_TIMESTAMP
                    """, config_key, config_value_str)
            return True
        except Exception as e:
            logger.error(f"闂佸綊娼х紞濠囧闯濞差亜鍗抽悗娑櫳戦悡鈧梺缁樼矤閸ㄤ即銆傞妸鈺佺煑婵せ鍋撻柛锝囧劋瀵板嫭娼忛銉? {e}")
            return False
        finally:
            await conn.close()

    success = run_async(batch_update_async())
    return jsonify({'success': success})

@app.route('/email_fetch')
def email_fetch():
    """闂備緡鍙庨崰姘额敊閸儱鐭楅柡宓啫鈻忔俊鐐€楅弫璇差焽?""
    return render_template_string(EMAIL_FETCH_TEMPLATE)

@app.route('/api/shan_mail/balance')
def get_shan_mail_balance():
    """闂佸吋鍎抽崲鑼躲亹閸ヮ剚鈷掓い蹇撶墕娴犲繒绱掗悩鎻掔秮缂傚秵鍨堕敍?""
    async def get_balance_async():
        try:
            # 婵炲濮寸€涒晠寮抽悢鐓庣妞ゆ棁鍋愬銊╂煠閹冩Щ鐟滄澘娲濠氼敂閸繀绮＄紓浣哄█娴滃爼宕㈤妶鍥╃＞?            conn = await get_db_connection()
            card_key = await conn.fetchval("""
                SELECT config_value FROM email_config
                WHERE config_key = 'SHAN_MAIL_CARD_KEY'
            """)
            await conn.close()

            if not card_key:
                return {'success': False, 'message': '闂佸搫鐗滄禍顏堝储閵堝洨纾炬い鏇楀亾婵☆偒鍨堕弻鍥敊缂併垹鏁婚梺鍛娿仜閳ь剙纾Σ?}

            # 闁诲海鏁搁崢褔宕ｉ崱娑氬祦闁哄牓娼ч埢蹇涙煟閳垛晛鈼anMailProvider
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
            from shan_mail_provider import ShanMailProvider

            provider = ShanMailProvider(card_key)
            balance = provider.get_balance()

            if balance is not None:
                return {'success': True, 'balance': balance}
            else:
                return {'success': False, 'message': '闂佸搫琚崕鎾敋濡や焦濯存繛鍡樻惄閺夊搫顭块幆鎵翱閻?}

        except Exception as e:
            logger.error(f"闂佸吋鍎抽崲鑼躲亹閸ヮ剚鈷掓い蹇撶墕娴犲繒绱掗悩鎻掔秮缂傚秵鍨堕敍鎰攽閸℃劒鏉柣? {e}")
            return {'success': False, 'message': str(e)}

    result = run_async(get_balance_async())
    return jsonify(result)

@app.route('/api/shan_mail/stock')
def get_shan_mail_stock():
    """闂佸吋鍎抽崲鑼躲亹閸ヮ剚鈷掓い蹇撶墕娴犲繒绱掗悩鎻掕埞缂併劏浜埀?""
    async def get_stock_async():
        try:
            # 婵炲濮寸€涒晠寮抽悢鐓庣妞ゆ棁鍋愬銊╂煠閹冩Щ鐟滄澘娲濠氼敂閸繀绮＄紓浣哄█娴滃爼宕㈤妶鍥╃＞?            conn = await get_db_connection()
            card_key = await conn.fetchval("""
                SELECT config_value FROM email_config
                WHERE config_key = 'SHAN_MAIL_CARD_KEY'
            """)
            await conn.close()

            if not card_key:
                return {'success': False, 'message': '闂佸搫鐗滄禍顏堝储閵堝洨纾炬い鏇楀亾婵☆偒鍨堕弻鍥敊缂併垹鏁婚梺鍛娿仜閳ь剙纾Σ?}

            # 闁诲海鏁搁崢褔宕ｉ崱娑氬祦闁哄牓娼ч埢蹇涙煟閳垛晛鈼anMailProvider
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
            from shan_mail_provider import ShanMailProvider

            provider = ShanMailProvider(card_key)
            stock = provider.get_stock()

            if stock is not None:
                return {'success': True, 'stock': stock}
            else:
                return {'success': False, 'message': '闂佸搫琚崕鎾敋濡や焦鍎熼柟鎯х－閹界姴顭块幆鎵翱閻?}

        except Exception as e:
            logger.error(f"闂佸吋鍎抽崲鑼躲亹閸ヮ剚鈷掓い蹇撶墕娴犲繒绱掗悩鎻掕埞缂併劏浜埀顒佺⊕閿氶柕鍥ㄥ灩閹? {e}")
            return {'success': False, 'message': str(e)}

    result = run_async(get_stock_async())
    return jsonify(result)

@app.route('/api/shan_mail/fetch', methods=['POST'])
def fetch_shan_mail():
    """婵炲濮撮柊锝呂涢鐐寸劷妞ゆ梻铏庨崬鎼佹煕濞嗘劗澧憸?""
    data = request.json
    count = data.get('count', 1)
    email_type = data.get('email_type', 'outlook')

    async def fetch_emails_async():
        try:
            # 婵炲濮寸€涒晠寮抽悢鐓庣妞ゆ棁鍋愬銊╂煠閹冩Щ鐟滄澘娲濠氼敂閸繀绮＄紓浣哄█娴滃爼宕㈤妶鍥╃＞?            conn = await get_db_connection()
            card_key = await conn.fetchval("""
                SELECT config_value FROM email_config
                WHERE config_key = 'SHAN_MAIL_CARD_KEY'
            """)

            if not card_key:
                await conn.close()
                return {'success': False, 'message': '闂佸搫鐗滄禍顏堝储閵堝洨纾炬い鏇楀亾婵☆偒鍨堕弻鍥敊缂併垹鏁婚梺鍛娿仜閳ь剙纾Σ?}

            # 闁诲海鏁搁崢褔宕ｉ崱娑氬祦闁哄牓娼ч埢蹇涙煟閳垛晛鈼anMailProvider
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
            from shan_mail_provider import ShanMailProvider

            provider = ShanMailProvider(card_key)

            # 濠碘槅鍋€閸嬫捇鏌＄仦璇插姍缂傚秵鍨堕敍?            balance = provider.get_balance()
            if balance is None or balance < count:
                await conn.close()
                return {'success': False, 'message': f'婵炶揪绲鹃悷鈺吢烽崒娑氣枖鐎广儱鐗嗛崰鏇㈡煥濞戞瀚扮紓宥咁儔瀹曟粌顓奸崟顓犫枏婵? {balance}'}

            # 闂佸湱绮崝鏇°亹閸ヮ剚鐒芥い鏃傝檸閸?
            email_tokens = provider.fetch_emails(count, email_type)
            if not email_tokens:
                await conn.close()
                return {'success': False, 'message': '闂佸湱绮崝鏇°亹閸ヮ剚鐒芥い鏃傝檸閸炵顭块幆鎵翱閻?}

            # 闁荤喐鐟辩徊楣冩倵娴犲宓侀柤鎼佹涧濞兼垿鏌涢弮鍌毿㈤柛鈺佺焸瀵偊鎮ч崼婵堛偊闁?            added_accounts = []
            failed_accounts = []

            for email_token in email_tokens:
                parsed = provider.parse_email_token(email_token)
                if parsed:
                    try:
                        # 濠电儑缍€椤曆勬叏閻愬搫绀嗛柣妤€鐗婂▓鍫曟煙鐠団€虫灈缂?                        await conn.execute("""
                            INSERT INTO email_accounts (email, password, client_id, access_token, provider)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (email) DO UPDATE SET
                                password = EXCLUDED.password,
                                client_id = EXCLUDED.client_id,
                                access_token = EXCLUDED.access_token,
                                provider = EXCLUDED.provider,
                                is_active = true,
                                updated_at = CURRENT_TIMESTAMP
                        """, parsed['email'], parsed['password'], parsed['client_id'],
                             parsed['access_token'], email_type)

                        added_accounts.append(parsed['email'])
                    except Exception as e:
                        logger.error(f"濠电儑缍€椤曆勬叏閻愮儤鐒芥い鏃傝檸閸炴悂鏌涢幒鏂款暭闁哄棛鍠栭獮鎴︻敊閼测晜鐨戞繝銏″劶缁墽鎲? {e}")
                        failed_accounts.append(parsed['email'])
                else:
                    failed_accounts.append(email_token)

            await conn.close()

            return {
                'success': True,
                'message': f'闂佺懓鐡ㄩ崝鏇熸叏濞戞〒搴ｆ嫚閹绘帩娼?{len(added_accounts)} 婵炴垶鎼╂禍顏堝磻閺嶎偆涓?,
                'added_accounts': added_accounts,
                'failed_accounts': failed_accounts,
                'total_requested': count,
                'total_added': len(added_accounts)
            }

        except Exception as e:
            logger.error(f"闂傚倸鍋嗘禍顏堝磻閺嶎偆涓嶉柛妤冨仜缁插潡鏌涘▎蹇撴Щ闁靛洦鍨归幏? {e}")
            return {'success': False, 'message': str(e)}

    result = run_async(fetch_emails_async())
    return jsonify(result)

@app.route('/api/github/login', methods=['POST'])
def github_login():
    """GitHub闂佽皫鍡╁殭缂傚秴绉归獮鎺楀Ψ閵夈儳绋?""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    tfa_secret = data.get('tfa_secret')
    headless = data.get('headless', False)

    if not username or not password:
        return jsonify({
            'success': False,
            'message': '闂佹椿娼块崝宥夊春濞戙垹瑙︾€广儱鎳忕€氭煡鎮楅棃娑欘棤闁绘牗绮嶇粙澶婎吋閸繂骞嬫繛鎴炴崄濞咃綁鍩?
        })

    try:
        # 闁诲海鏁搁崢褔宕ｉ崪绌抰Hub闂佽皫鍡╁殭缂傚秴绉归幊妯侯潩椤撶喐瀚?
        import subprocess
        import json
        import os

        # 闂佸搫顑呯€氼剛绱撻幘璇插窛闁瑰瓨甯楁慨?
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts', 'github_login.py')
        cmd = ['python', script_path, username, password]

        if tfa_secret:
            cmd.append(tfa_secret)
        else:
            cmd.append('')  # 闂佸憡顨堟慨宕囩礊閸涱垳绠?
        cmd.append('true' if headless else 'false')

        logger.info(f"闂佸湱鐟抽崱鈺傛杸GitHub闂佽皫鍡╁殭缂傚秴绉瑰畷銊╁箣閹烘挸袘: {' '.join(cmd[:3])} [闁诲酣娼уΛ娑㈡偉濠婂喚鍟呴柡灞诲劜椤撴椽鏌﹀Ο鐑樼拨 ...")

        # 闂佸湱鐟抽崱鈺傛杸闂佽皫鍡╁殭缂傚秴绉归幊妯侯潩椤撶喐瀚?
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2闂佸憡甯掑Λ婵嬪箰閹捐埖鎯ラ柛娑卞枟椤?
        )

        if result.returncode == 0:
            # 闁荤喐鐟辩徊楣冩倵閼恒儲浜ら柡鍌涘缁€鈧紓鍌欑劍閹稿鎮?            try:
                login_result = json.loads(result.stdout)

                # 婵犵鈧啿鈧綊鎮樻径鎰剬閻犲洩灏欑粔鍧楁煙鐎涙ê濮囧┑顔界洴閺佸秶浠﹂悙顒傚嚱闂佸搫鍊绘晶妤呭汲閻旂厧绠叉い鏃囧亹濮樸劌鈽夐幙鍐ㄥ箻婵炲牊鍨堕幏鍛崉閵婏附娈㈤柣鐘辩劍濠㈡绱?                if login_result.get('success'):
                    async def update_usage():
                        conn = await get_db_connection()
                        try:
                            # 闂佸搫绉烽～澶婄暤娓氣偓閹粙濡搁敃鈧悡鏇㈡煕濮橆剛鈻岀紒杈ㄧ懇閺屽洭顢欑紒銏犳暬闂佹寧绋戦ˇ鏉棵洪崸妤€妫樺Λ棰佺閳诲繘鏌ｉ～顒€濮€妞ゆ柨娲╅妵?                            await conn.execute("""
                                UPDATE email_accounts
                                SET usage_count = COALESCE(usage_count, 0) + 1,
                                    last_used_at = CURRENT_TIMESTAMP,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE email = $1 AND is_active = true
                            """, username)
                            logger.info(f"閻庡湱顭堝璺好洪崸妤€妫橀柣褍绌紅Hub闂佽皫鍡╁殭缂傚秴绉甸幏鍛崉閵婏附娈㈤柣鐘辩劍濠㈡绱? {username}")
                        except Exception as e:
                            logger.error(f"闂佸搫娲ら悺銊╁蓟婵犲啯濯撮悹鎭掑妽閺嗗繘鎮规担瑙勭凡缂傚秴绉靛鍕綇椤愩儛? {e}")
                        finally:
                            await conn.close()

                    # 閻庢鍠栭崐褰掝敆閻愬搫鍗抽悗娑櫳戦悡鈧梺杞拌兌婢ф鐣垫担瑙勫劅?                    run_async(update_usage())

                return jsonify(login_result)
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'message': f'闂佽皫鍡╁殭缂傚秴绉归幊妯侯潩椤撶喐瀚抽柡澶嗘櫆閺屻劌煤閺嶎厼鍐€闁绘挸娴风涵鈧梻浣瑰閻熴劑顢? {result.stdout}'
                })
        else:
            return jsonify({
                'success': False,
                'message': f'闂佽皫鍡╁殭缂傚秴绉归幊妯侯潩椤撶喐瀚抽梺鍦懗閸♀晜鏂€婵犮垺鍎肩划鍓ф喆? {result.stderr}'
            })

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': '闂佽皫鍡╁殭缂傚秴绉堕幖楣冨川椤旂瓔妲梺鎸庣☉閻線顢氶鈧灋闁逞屽墴瀵濡疯缁夊湱绱撴担鍦煄缂佺粯鐩獮鎺楀Ψ閿曗偓閻忔鏌熼棃娑卞剰濠殿喒鏅濋埀顒傛嚀閺堫剟宕瑰顓ф鐎光偓閸愵亝顫?
        })
    except Exception as e:
        logger.error(f"GitHub闂佽皫鍡╁殭缂傚秴绉归獮鎺楀Ψ閵夈儳绋夐悗娈垮枛閸婃悂鎮? {e}")
        return jsonify({
            'success': False,
            'message': f'闂佽皫鍡╁殭缂傚秴绉归獮鎺楀Ψ閵夈儳绋夐悗娈垮枛閸婃悂鎮? {str(e)}'
        })

if __name__ == '__main__':
    print("濡絽鍟悾?闂佸憡鍑归崹鐗堟叏?Navie 闂備緡鍙庨崰姘额敊閸垻涓嶉柨娑樺閸婄偤鏌?..")
    print("濡絽鍟幉?闁荤姳绀佸鈥澄涢崼鏇炴嵍闁哄瀵х徊? http://localhost:5000")
    print("濡絽鍟埛鏃堟煥?缂佺虎鍙庨崰鏇犳崲濮濆嵀stgreSQL闂佽桨鑳舵晶妤€鐣垫担瑙勫劅闁圭偓鎯岄崝鈧梺闈╄礋閸斿繒鎹㈠鍥ㄥ仒?)
    app.run(host='0.0.0.0', port=5000, debug=True)
