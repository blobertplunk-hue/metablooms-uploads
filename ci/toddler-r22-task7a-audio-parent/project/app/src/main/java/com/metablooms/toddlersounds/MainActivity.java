package com.metablooms.toddlersounds;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import com.android.billingclient.api.AcknowledgePurchaseParams;
import com.android.billingclient.api.BillingClient;
import com.android.billingclient.api.BillingClientStateListener;
import com.android.billingclient.api.BillingFlowParams;
import com.android.billingclient.api.BillingResult;
import com.android.billingclient.api.PendingPurchasesParams;
import com.android.billingclient.api.ProductDetails;
import com.android.billingclient.api.Purchase;
import com.android.billingclient.api.PurchasesUpdatedListener;
import com.android.billingclient.api.QueryProductDetailsParams;
import com.android.billingclient.api.QueryProductDetailsResult;
import com.android.billingclient.api.QueryPurchasesParams;

import org.json.JSONObject;

import java.util.Collections;
import java.util.Locale;
import java.util.List;

public final class MainActivity extends Activity implements PurchasesUpdatedListener {
    private static final String PRODUCT_ID = "unlock_all_sounds";
    private static final String PIN = "1111";
    private static final String PREFS = "r22_entitlement";
    private static final String PREF_UNLOCKED = "full_unlock";
    private static final int IMMERSIVE_FLAGS = View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
            | View.SYSTEM_UI_FLAG_FULLSCREEN
            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_STABLE;

    private WebView webView;
    private BillingClient billingClient;
    private ProductDetails unlockProduct;
    private ProductDetails.OneTimePurchaseOfferDetails unlockOffer;
    private SharedPreferences prefs;
    private TextToSpeech textToSpeech;
    private volatile boolean textToSpeechReady;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        webView = new WebView(this);
        configureWebView();
        startTextToSpeech();
        setContentView(webView);
        restoreImmersiveMode();
        try { startLockTask(); } catch (RuntimeException ignored) { }
        webView.loadUrl("file:///android_asset/index.html");
        startBilling();
    }

    private void configureWebView() {
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(false);
        webView.getSettings().setDatabaseEnabled(false);
        webView.getSettings().setAllowContentAccess(false);
        webView.getSettings().setAllowFileAccess(true);
        webView.getSettings().setBlockNetworkLoads(true);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return request.getUrl() == null || !"file".equals(request.getUrl().getScheme());
            }
        });
        webView.addJavascriptInterface(new AndroidBridge(), "AndroidBridge");
    }

    private void startTextToSpeech() {
        textToSpeech = new TextToSpeech(this, status -> {
            if (status != TextToSpeech.SUCCESS || textToSpeech == null) {
                textToSpeechReady = false;
                return;
            }
            int languageResult = textToSpeech.setLanguage(Locale.US);
            textToSpeechReady = languageResult != TextToSpeech.LANG_MISSING_DATA
                    && languageResult != TextToSpeech.LANG_NOT_SUPPORTED;
            textToSpeech.setSpeechRate(0.88f);
            textToSpeech.setPitch(1.03f);
            textToSpeech.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                @Override
                public void onStart(String utteranceId) { }

                @Override
                public void onDone(String utteranceId) {
                    notifyLabelFinished(utteranceId, true);
                }

                @Override
                public void onError(String utteranceId) {
                    notifyLabelFinished(utteranceId, false);
                }

                @Override
                public void onStop(String utteranceId, boolean interrupted) {
                    notifyLabelFinished(utteranceId, false);
                }
            });
        });
    }

    private void notifyLabelFinished(String utteranceId, boolean success) {
        if (utteranceId == null || !utteranceId.startsWith("label-")) return;
        String ticket = utteranceId.substring("label-".length());
        try {
            Integer.parseInt(ticket);
        } catch (NumberFormatException ignored) {
            return;
        }
        runJs("window.onNativeLabelFinished(" + ticket + "," + success + ");");
    }

    private void restoreImmersiveMode() {
        getWindow().getDecorView().setSystemUiVisibility(IMMERSIVE_FLAGS);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) restoreImmersiveMode();
    }

    @Override
    protected void onResume() {
        super.onResume();
        restoreImmersiveMode();
        if (billingClient != null && billingClient.isReady()) queryOwnedPurchases();
    }

    @Override
    public void onBackPressed() {
        restoreImmersiveMode();
    }

    @Override
    protected void onDestroy() {
        if (billingClient != null) billingClient.endConnection();
        if (textToSpeech != null) {
            textToSpeech.stop();
            textToSpeech.shutdown();
        }
        if (webView != null) webView.destroy();
        super.onDestroy();
    }

    private void startBilling() {
        billingClient = BillingClient.newBuilder(this)
                .setListener(this)
                .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
                .enableAutoServiceReconnection()
                .build();
        billingClient.startConnection(new BillingClientStateListener() {
            @Override
            public void onBillingSetupFinished(BillingResult billingResult) {
                if (billingResult.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                    queryProduct();
                    queryOwnedPurchases();
                } else {
                    notifyBillingState("billing_unavailable");
                }
            }

            @Override
            public void onBillingServiceDisconnected() {
                notifyBillingState("billing_disconnected");
            }
        });
    }

    private void queryProduct() {
        QueryProductDetailsParams.Product product = QueryProductDetailsParams.Product.newBuilder()
                .setProductId(PRODUCT_ID)
                .setProductType(BillingClient.ProductType.INAPP)
                .build();
        QueryProductDetailsParams params = QueryProductDetailsParams.newBuilder()
                .setProductList(Collections.singletonList(product))
                .build();
        billingClient.queryProductDetailsAsync(params, this::onProductDetails);
    }

    private void onProductDetails(BillingResult result, QueryProductDetailsResult detailsResult) {
        if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
            notifyBillingState("product_unavailable");
            return;
        }
        List<ProductDetails> details = detailsResult.getProductDetailsList();
        if (details == null || details.isEmpty()) {
            notifyBillingState("product_unavailable");
            return;
        }
        unlockProduct = details.get(0);
        List<ProductDetails.OneTimePurchaseOfferDetails> offers = unlockProduct.getOneTimePurchaseOfferDetailsList();
        if (offers == null || offers.isEmpty()) {
            notifyBillingState("offer_unavailable");
            return;
        }
        unlockOffer = offers.get(0);
        final String price = unlockOffer.getFormattedPrice();
        runJs("window.onNativeProductInfo(" + JSONObject.quote(price) + ");");
    }

    private void queryOwnedPurchases() {
        QueryPurchasesParams params = QueryPurchasesParams.newBuilder()
                .setProductType(BillingClient.ProductType.INAPP)
                .build();
        billingClient.queryPurchasesAsync(params, (result, purchases) -> {
            if (result.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                processPurchases(purchases, true);
            }
        });
    }

    @Override
    public void onPurchasesUpdated(BillingResult result, List<Purchase> purchases) {
        if (result.getResponseCode() == BillingClient.BillingResponseCode.OK && purchases != null) {
            processPurchases(purchases, false);
        } else if (result.getResponseCode() == BillingClient.BillingResponseCode.ITEM_ALREADY_OWNED) {
            queryOwnedPurchases();
        } else if (result.getResponseCode() != BillingClient.BillingResponseCode.USER_CANCELED) {
            notifyBillingState("purchase_error");
        }
    }

    private void processPurchases(List<Purchase> purchases, boolean authoritativeQuery) {
        boolean foundPurchased = false;
        if (purchases != null) {
            for (Purchase purchase : purchases) {
                if (!purchase.getProducts().contains(PRODUCT_ID)) continue;
                if (purchase.getPurchaseState() == Purchase.PurchaseState.PENDING) {
                    notifyBillingState("purchase_pending");
                    continue;
                }
                if (purchase.getPurchaseState() != Purchase.PurchaseState.PURCHASED) continue;
                foundPurchased = true;
                grantEntitlement();
                if (!purchase.isAcknowledged()) {
                    AcknowledgePurchaseParams params = AcknowledgePurchaseParams.newBuilder()
                            .setPurchaseToken(purchase.getPurchaseToken())
                            .build();
                    billingClient.acknowledgePurchase(params, result -> {
                        if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                            notifyBillingState("acknowledgement_retry_needed");
                        }
                    });
                }
            }
        }
        if (authoritativeQuery && !foundPurchased) setEntitlement(false, "not_owned");
    }

    private void grantEntitlement() {
        setEntitlement(true, "purchased");
    }

    private void setEntitlement(boolean unlocked, String status) {
        prefs.edit().putBoolean(PREF_UNLOCKED, unlocked).apply();
        runJs("window.onNativeEntitlementChanged(" + unlocked + "," + JSONObject.quote(status) + ");");
    }

    private void notifyBillingState(String status) {
        runJs("window.onNativeBillingState(" + JSONObject.quote(status) + ");");
    }

    private void runJs(String script) {
        runOnUiThread(() -> {
            if (webView != null) webView.evaluateJavascript(script, null);
        });
    }

    private void launchUnlockFlow() {
        if (billingClient == null || !billingClient.isReady() || unlockProduct == null || unlockOffer == null) {
            notifyBillingState("billing_not_ready");
            if (billingClient != null && billingClient.isReady()) queryProduct();
            return;
        }
        BillingFlowParams.ProductDetailsParams productParams = BillingFlowParams.ProductDetailsParams.newBuilder()
                .setProductDetails(unlockProduct)
                .setOfferToken(unlockOffer.getOfferToken())
                .build();
        BillingFlowParams flowParams = BillingFlowParams.newBuilder()
                .setProductDetailsParamsList(Collections.singletonList(productParams))
                .setIsOfferPersonalized(false)
                .build();
        BillingResult result = billingClient.launchBillingFlow(this, flowParams);
        if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
            notifyBillingState("purchase_launch_error");
        }
    }

    public final class AndroidBridge {
        @JavascriptInterface
        public boolean isUnlocked() {
            return prefs.getBoolean(PREF_UNLOCKED, false);
        }

        @JavascriptInterface
        public void speakLabel(String label, int ticket) {
            if (label == null || label.trim().isEmpty()) {
                runJs("window.onNativeLabelFinished(" + ticket + ",false);");
                return;
            }
            runOnUiThread(() -> {
                if (!textToSpeechReady || textToSpeech == null) {
                    runJs("window.onNativeLabelFinished(" + ticket + ",false);");
                    return;
                }
                String utteranceId = "label-" + ticket;
                int result = textToSpeech.speak(label, TextToSpeech.QUEUE_FLUSH, null, utteranceId);
                if (result == TextToSpeech.ERROR) {
                    runJs("window.onNativeLabelFinished(" + ticket + ",false);");
                }
            });
        }

        @JavascriptInterface
        public void requestUnlock(String pin) {
            if (!PIN.equals(pin)) return;
            runOnUiThread(MainActivity.this::launchUnlockFlow);
        }

        @JavascriptInterface
        public void requestRestore(String pin) {
            if (!PIN.equals(pin)) return;
            runOnUiThread(() -> {
                if (billingClient != null && billingClient.isReady()) queryOwnedPurchases();
                else notifyBillingState("billing_not_ready");
            });
        }

        @JavascriptInterface
        public void requestExit(String pin) {
            if (!PIN.equals(pin)) return;
            runOnUiThread(() -> {
                ActivityManager activityManager = (ActivityManager) getSystemService(ACTIVITY_SERVICE);
                try {
                    if (activityManager != null
                            && activityManager.getLockTaskModeState() != ActivityManager.LOCK_TASK_MODE_NONE) {
                        stopLockTask();
                    }
                } catch (RuntimeException error) {
                    runJs("window.onNativeExitState(\"unpin_failed\");");
                    return;
                }
                runJs("window.onNativeExitState(\"exiting\");");
                getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE);
                finishAndRemoveTask();
            });
        }
    }
}
