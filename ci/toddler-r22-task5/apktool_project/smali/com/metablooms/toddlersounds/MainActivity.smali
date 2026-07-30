.class public Lcom/metablooms/toddlersounds/MainActivity;
.super Landroid/app/Activity;
.source "MainActivity.java"

.field private webView:Landroid/webkit/WebView;

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method

.method private applyImmersiveMode()V
    .locals 2
    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;
    move-result-object v0
    invoke-virtual {v0}, Landroid/view/Window;->getDecorView()Landroid/view/View;
    move-result-object v0
    const/16 v1, 0x1706
    invoke-virtual {v0, v1}, Landroid/view/View;->setSystemUiVisibility(I)V
    return-void
.end method

.method private showSystemBars()V
    .locals 2
    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;
    move-result-object v0
    invoke-virtual {v0}, Landroid/view/Window;->getDecorView()Landroid/view/View;
    move-result-object v0
    const/4 v1, 0x0
    invoke-virtual {v0, v1}, Landroid/view/View;->setSystemUiVisibility(I)V
    return-void
.end method

.method protected onCreate(Landroid/os/Bundle;)V
    .locals 5
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;
    move-result-object v4
    const/16 v2, 0x80
    invoke-virtual {v4, v2}, Landroid/view/Window;->addFlags(I)V
    invoke-direct {p0}, Lcom/metablooms/toddlersounds/MainActivity;->applyImmersiveMode()V

    new-instance v0, Landroid/webkit/WebView;
    invoke-direct {v0, p0}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V
    iput-object v0, p0, Lcom/metablooms/toddlersounds/MainActivity;->webView:Landroid/webkit/WebView;

    invoke-virtual {v0}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v1
    const/4 v2, 0x1
    invoke-virtual {v1, v2}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V
    invoke-virtual {v1, v2}, Landroid/webkit/WebSettings;->setDomStorageEnabled(Z)V
    const/4 v3, 0x0
    invoke-virtual {v1, v3}, Landroid/webkit/WebSettings;->setMediaPlaybackRequiresUserGesture(Z)V
    invoke-virtual {v1, v3}, Landroid/webkit/WebSettings;->setSupportZoom(Z)V
    invoke-virtual {v1, v3}, Landroid/webkit/WebSettings;->setBuiltInZoomControls(Z)V
    invoke-virtual {v1, v3}, Landroid/webkit/WebSettings;->setDisplayZoomControls(Z)V
    const/16 v2, 0x64
    invoke-virtual {v1, v2}, Landroid/webkit/WebSettings;->setTextZoom(I)V

    invoke-virtual {v0, v3}, Landroid/view/View;->setLongClickable(Z)V
    const v2, -0x000528
    invoke-virtual {v0, v2}, Landroid/webkit/WebView;->setBackgroundColor(I)V
    invoke-virtual {p0, v0}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V

    const-string v1, "AndroidBridge"
    invoke-virtual {v0, p0, v1}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    const-string v1, "file:///android_asset/index.html"
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V

    invoke-virtual {p0}, Landroid/app/Activity;->startLockTask()V
    return-void
.end method

.method protected onWindowFocusChanged(Z)V
    .locals 0
    invoke-super {p0, p1}, Landroid/app/Activity;->onWindowFocusChanged(Z)V
    if-eqz p1, :done
    invoke-direct {p0}, Lcom/metablooms/toddlersounds/MainActivity;->applyImmersiveMode()V
:done
    return-void
.end method

.method public onBackPressed()V
    .locals 0
    return-void
.end method

.method public requestExit(Ljava/lang/String;)V
    .locals 1
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    const-string v0, "1111"
    invoke-virtual {v0, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :done

    invoke-virtual {p0}, Landroid/app/Activity;->stopLockTask()V
    invoke-direct {p0}, Lcom/metablooms/toddlersounds/MainActivity;->showSystemBars()V
    invoke-virtual {p0}, Landroid/app/Activity;->finish()V
:done
    return-void
.end method

.method protected onPause()V
    .locals 1
    iget-object v0, p0, Lcom/metablooms/toddlersounds/MainActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :done
    invoke-virtual {v0}, Landroid/webkit/WebView;->onPause()V
:done
    invoke-super {p0}, Landroid/app/Activity;->onPause()V
    return-void
.end method

.method protected onResume()V
    .locals 1
    invoke-super {p0}, Landroid/app/Activity;->onResume()V
    invoke-direct {p0}, Lcom/metablooms/toddlersounds/MainActivity;->applyImmersiveMode()V
    iget-object v0, p0, Lcom/metablooms/toddlersounds/MainActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :done
    invoke-virtual {v0}, Landroid/webkit/WebView;->onResume()V
:done
    return-void
.end method

.method protected onDestroy()V
    .locals 1
    iget-object v0, p0, Lcom/metablooms/toddlersounds/MainActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :done
    invoke-virtual {v0}, Landroid/webkit/WebView;->destroy()V
:done
    invoke-super {p0}, Landroid/app/Activity;->onDestroy()V
    return-void
.end method
