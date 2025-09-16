

## Roxyclient

继续我们要进一步的学习，因此我们需要自己创建一个 Roxyclient 的 类，调用自定义的 浏览器

请你查看文档：
https://faq.roxybrowser.com/zh/api-documentation/api-endpoint.html

这里提供了 python 调用 selenium的例子。同样我们构建一个 class RoxyClient 在utils 当中统一管理 浏览器通信请求。

我们需要 这个class 有 

/browser/workspace：得到workspaceId
/browser/create：创建窗口
/browser/random_env：随机指纹
/browser/open：打开窗口


程序退出的时候应该运行关闭和删除
/browser/close
/browser/delete


我们需要将 之前使用的 chrome 浏览器 替换成 roxyclient

## 进一步完善我们最初的设想

github的注册任务已经完成了，现在我们要进一步进入我们最初的需求。下面的任务很复杂，请你仔细理解然后整理出 完善的流程task 和我讨论。

并且在中途遇到问题要 不耻下问。下面的任务是 接在 我们之前的 github 任务之后的。

### 任务一 注册aug



进入 https://app.augmentcode.com/，点击这个按钮<a data-slot="button" class="cursor-pointer inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium disabled:pointer-events-none disabled:opacity-50 [&amp;_svg]:pointer-events-none [&amp;_svg:not([class*='size-'])]:size-4 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive text-foreground border border-border shadow-xs transition-all duration-200 ease-out hover:text-accent-foreground hover-golden h-9 px-4 py-2 has-[&gt;svg]:px-3 rounded-md" href="https://app.augmentcode.com">Sign in</a>

等待页面跳转然后点击

<button type="submit" class="c2cff1259 c918693c8 c8ba0bd94" data-provider="github" data-action-button-secondary="true">
                    
                      <span class="ce42770cf c390c7ad5" data-provider="github"></span>
                    
                  
                    <span class="cc2f84869">Continue with GitHub</span>
</button>

等待这个按钮激活然后点击：

<button data-octo-click="oauth_application_authorization" data-octo-dimensions="marketplace_listing_id:,came_from_marketplace:false,paid_marketplace_plan_purchased:false" data-ga-click="Oauth, oauth application authorized, oauth_application_id:2869345; listing_id:; came_from_integrations_directory:false; came_from_marketplace:false; paid_marketplace_plan_purchased:false; marketplace_listing_id:" type="submit" name="authorize" value="1" class="js-oauth-authorize-btn btn btn-primary width-full ws-normal">Authorize augmentcode</button>

等待页面重定向。检测页面是否出现 signup-rejected 按钮。

这里有一个判断，如果 重定向至 https://app.augmentcode.com/account/subscription，我们进入下面的流程。如果没有成功，那就退出，将 本次使用的 {"email": "password":  "tfa_secret": "client_id": "access_token"}写入到 flaged.json 文件中。

如果重定向成功，等待下面的 按钮出现，然后点击：
<button data-accent-color="" class="rt-reset rt-BaseButton rt-r-size-2 rt-variant-solid rt-Button">Confirm payment method</button>

等待重定向至https://billing.augmentcode.com/

下面需要你使用playwright 进一步的思考，这是一个stripe 的 绑定卡单页面。有一些iframe

- 输入卡号<input class="CheckoutInput CheckoutInput--tabularnums Input Input--empty" autocomplete="cc-number" autocorrect="off" spellcheck="false" id="cardNumber" name="cardNumber" type="text" inputmode="numeric" aria-label="Card number" placeholder="1234 1234 1234 1234" aria-invalid="false" aria-describedby="" data-1p-ignore="false" data-lp-ignore="false" value="">
- 输入年月 <input class="CheckoutInput CheckoutInput--tabularnums Input Input--empty" autocomplete="cc-exp" autocorrect="off" spellcheck="false" id="cardExpiry" name="cardExpiry" type="text" inputmode="numeric" aria-label="Expiration" placeholder="MM / YY" aria-invalid="false" aria-describedby="" data-1p-ignore="false" data-lp-ignore="false" value="">
- 输入 cvc <input class="CheckoutInput CheckoutInput--tabularnums Input Input--empty" autocomplete="cc-csc" autocorrect="off" spellcheck="false" id="cardCvc" name="cardCvc" type="text" inputmode="numeric" aria-label="CVC" placeholder="CVC" aria-invalid="false" aria-describedby="" data-1p-ignore="false" data-lp-ignore="false" value="">
- 点击手动输入地址 <span class="Button-textCheckoutSecondary Text Text-color--gray400 Text-fontWeight--500 Text--truncate">Enter address manually</span>
- 输入地址行1<input class="CheckoutInput Input Input--empty" autocomplete="disabled" autocorrect="off" spellcheck="false" id="billingAddressLine1" name="billingAddressLine1" type="text" aria-label="Address line 1" placeholder="Address line 1" aria-invalid="false" aria-describedby="" data-1p-ignore="false" data-lp-ignore="false" value="">
- 输入地址行2 <input class="CheckoutInput Input Input--empty" autocomplete="billing address-line2" autocorrect="off" spellcheck="false" id="billingAddressLine2" name="billingAddressLine2" type="text" aria-label="Address line 2" placeholder="Address line 2" aria-invalid="false" aria-describedby="" data-1p-ignore="false" data-lp-ignore="false" value="">
- 输入postal code <input class="CheckoutInput Input Input--empty" autocomplete="billing postal-code" autocorrect="off" spellcheck="false" id="billingPostalCode" name="billingPostalCode" type="text" aria-label="Postal code" placeholder="Postal code" aria-invalid="false" aria-describedby="" data-1p-ignore="false" data-lp-ignore="false" value="">

可能会跳出 hcaptcha，yescaptch也提供了api，文档在：
https://yescaptcha.atlassian.net/wiki/spaces/YESCAPTCHA/pages/7929858/HCaptchaTaskProxyless+HCaptcha

他需要一些参数，先加一个 检测机制使用playwright检测。


等待跳转回 https://app.augmentcode.com/account/subscription。

### 任务二 解析token

1。 生成授权url

```js
    // 工具函数
    function base64URLEncode(buffer) {
        return btoa(String.fromCharCode.apply(null, new Uint8Array(buffer)))
            .replace(/\+/g, "-")
            .replace(/\//g, "_")
            .replace(/=/g, "");
    }

    async function sha256Hash(input) {
        const encoder = new TextEncoder();
        const data = encoder.encode(input);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        return hashBuffer;
    }

    async function createOAuthState() {
        // 生成随机字节
        const codeVerifierArray = new Uint8Array(32);
        window.crypto.getRandomValues(codeVerifierArray);
        const codeVerifier = base64URLEncode(codeVerifierArray.buffer);

        // 创建 code challenge
        const codeChallenge = base64URLEncode(await sha256Hash(codeVerifier));

        // 生成随机 state
        const stateArray = new Uint8Array(8);
        window.crypto.getRandomValues(stateArray);
        const state = base64URLEncode(stateArray.buffer);

        const oauthState = {
            codeVerifier,
            codeChallenge,
            state,
            creationTime: Date.now()
        };

        // 存储状态以供后续使用
        GM_setValue('oauthState', JSON.stringify(oauthState));

        return oauthState;
    }

    function generateAuthorizeURL(oauthState) {
        const params = new URLSearchParams({
            response_type: "code",
            code_challenge: oauthState.codeChallenge,
            client_id: clientID,
            state: oauthState.state,
            prompt: "login",
        });

        return `https://auth.augmentcode.com/authorize?${params.toString()}`;
    }
```

2. 重定向到上面生成的url

3。还是点击这个button <button type="submit" class="c2cff1259 c918693c8 c8ba0bd94" data-provider="github" data-action-button-secondary="true">
                    
                      <span class="ce42770cf c390c7ad5" data-provider="github"></span>
                    
                  
                    <span class="cc2f84869">Continue with GitHub</span>
</button>

4. 然后等待跳转页面到 

获取下列的元素

<input id="codeDisplay" class="code-display" type="text" value="{&quot;code&quot;: &quot;_039538960d035f06cbdb30addba4e0d5&quot;, &quot;state&quot;: &quot;VC3jKqsVXeI&quot;, &quot;tenant_url&quot;: &quot;https://d10.api.augmentcode.com/&quot;}" readonly="" aria-label="Authentication JSON data">

并且提取出 code 和 state，tenant_url

5. 得到token

    async function getAccessToken(tenant_url, codeVerifier, code) {
        // 确保tenant_url以/结尾
        if (!tenant_url.endsWith('/')) {
            tenant_url = tenant_url + '/';
        }

        console.log("正在请求token...");
        console.log("URL:", `${tenant_url}token`);
        console.log("codeVerifier:", codeVerifier);
        console.log("code:", code);

        const data = {
            grant_type: "authorization_code",
            client_id: clientID,
            code_verifier: codeVerifier,
            redirect_uri: "",
            code: code,
        };

        console.log("请求数据:", JSON.stringify(data));

        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: "POST",
                url: `${tenant_url}token`,
                headers: {
                    "Content-Type": "application/json"
                },
                data: JSON.stringify(data),
                onload: function(response) {
                    try {
                        console.log("API响应状态:", response.status);
                        console.log("API响应头:", response.responseHeaders);
                        console.log("API响应内容:", response.responseText);

                        const json = JSON.parse(response.responseText);
                        console.log("解析后的响应:", json);

                        if (json.access_token) {
                            resolve(json.access_token);
                        } else {
                            reject(`No access token found in response. Full response: ${JSON.stringify(json)}`);
                        }
                    } catch (e) {
                        reject(`Error parsing response: ${e}. Raw response: ${response.responseText}`);
                    }
                },
                onerror: function(error) {
                    console.error("请求错误:", error);
                    reject(`Request error: ${error}`);
                }
            });
        });
    }


6. 保存token

成功之后在 
navie_\augment_token.json
中将 

    {
      "email": "prhpfjh056@hotmail.com",
      "password": 
      "tfa_secret":
      "client_id": 
      "access_token":  # 这是邮箱的token
      "tenant_url":
      "augment_token":  # 这是augment的token
    }

写入