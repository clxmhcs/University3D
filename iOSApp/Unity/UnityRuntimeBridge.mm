#import "UnityRuntimeBridge.h"
#import <Foundation/Foundation.h>
#import <objc/message.h>
#import <objc/runtime.h>
#import <dlfcn.h>
#import <crt_externs.h>
#import <mach-o/ldsyms.h>

static id gUnityFramework = nil;
static JCUUnityMessageCallback gMessageCallback = nullptr;

typedef void (*RegisterUnityCallbackFn)(JCUUnityMessageCallback callback);

static id JCUCallId(id target, SEL selector)
{
    return ((id (*)(id, SEL))objc_msgSend)(target, selector);
}

static void JCURegisterNativeCallbackIfPossible(void)
{
    if (gMessageCallback == nullptr)
    {
        return;
    }

    auto registerCallback = (RegisterUnityCallbackFn)dlsym(RTLD_DEFAULT, "CampusBridge_RegisterCallback");
    if (registerCallback != nullptr)
    {
        registerCallback(gMessageCallback);
    }
}

static id JCULoadUnityFramework(void)
{
    if (gUnityFramework != nil)
    {
        return gUnityFramework;
    }

    NSString *frameworkPath = [[[NSBundle mainBundle] privateFrameworksPath]
        stringByAppendingPathComponent:@"UnityFramework.framework"];
    NSBundle *bundle = [NSBundle bundleWithPath:frameworkPath];
    if (bundle == nil || ![bundle load])
    {
        return nil;
    }

    Class frameworkClass = bundle.principalClass ?: NSClassFromString(@"UnityFramework");
    if (frameworkClass == Nil)
    {
        return nil;
    }

    SEL getInstance = sel_registerName("getInstance");
    gUnityFramework = JCUCallId((id)frameworkClass, getInstance);
    if (gUnityFramework == nil)
    {
        return nil;
    }

    SEL appControllerSelector = sel_registerName("appController");
    id appController = JCUCallId(gUnityFramework, appControllerSelector);
    if (appController == nil)
    {
        SEL setExecuteHeader = sel_registerName("setExecuteHeader:");
        ((void (*)(id, SEL, const struct mach_header *))objc_msgSend)(
            gUnityFramework,
            setExecuteHeader,
            &_mh_execute_header
        );
    }

    SEL setDataBundleId = sel_registerName("setDataBundleId:");
    ((void (*)(id, SEL, const char *))objc_msgSend)(
        gUnityFramework,
        setDataBundleId,
        "com.unity3d.framework"
    );

    JCURegisterNativeCallbackIfPossible();
    return gUnityFramework;
}

BOOL JCUUnityIsAvailable(void)
{
    NSString *frameworkPath = [[[NSBundle mainBundle] privateFrameworksPath]
        stringByAppendingPathComponent:@"UnityFramework.framework"];
    return [[NSFileManager defaultManager] fileExistsAtPath:frameworkPath];
}

void JCUUnitySetMessageCallback(JCUUnityMessageCallback callback)
{
    gMessageCallback = callback;
    JCURegisterNativeCallbackIfPossible();
}

void JCUUnityStart(void)
{
    id framework = JCULoadUnityFramework();
    if (framework == nil)
    {
        return;
    }

    id appController = JCUCallId(framework, sel_registerName("appController"));
    if (appController != nil)
    {
        return;
    }

    SEL runEmbedded = sel_registerName("runEmbeddedWithArgc:argv:appLaunchOpts:");
    ((void (*)(id, SEL, int, char **, NSDictionary *))objc_msgSend)(
        framework,
        runEmbedded,
        *_NSGetArgc(),
        *_NSGetArgv(),
        nil
    );

    JCURegisterNativeCallbackIfPossible();
}

UIViewController *JCUUnityViewController(void)
{
    id framework = JCULoadUnityFramework();
    if (framework == nil)
    {
        return nil;
    }

    id appController = JCUCallId(framework, sel_registerName("appController"));
    if (appController == nil)
    {
        return nil;
    }

    return (UIViewController *)JCUCallId(appController, sel_registerName("rootViewController"));
}

void JCUUnityShow(void)
{
    id framework = JCULoadUnityFramework();
    if (framework != nil)
    {
        ((void (*)(id, SEL))objc_msgSend)(framework, sel_registerName("showUnityWindow"));
    }
}

void JCUUnityUnload(void)
{
    if (gUnityFramework != nil)
    {
        ((void (*)(id, SEL))objc_msgSend)(gUnityFramework, sel_registerName("unloadApplication"));
        gUnityFramework = nil;
    }
}

void JCUUnitySendMessage(const char *gameObject, const char *method, const char *message)
{
    id framework = JCULoadUnityFramework();
    if (framework == nil)
    {
        return;
    }

    SEL sendMessage = sel_registerName("sendMessageToGOWithName:functionName:message:");
    ((void (*)(id, SEL, const char *, const char *, const char *))objc_msgSend)(
        framework,
        sendMessage,
        gameObject,
        method,
        message
    );
}
