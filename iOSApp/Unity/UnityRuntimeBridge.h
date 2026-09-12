#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN

typedef void (*JCUUnityMessageCallback)(const char *json);

BOOL JCUUnityIsAvailable(void);
void JCUUnitySetMessageCallback(JCUUnityMessageCallback _Nullable callback);
void JCUUnityStart(void);
UIViewController * _Nullable JCUUnityViewController(void);
void JCUUnityShow(void);
void JCUUnityUnload(void);
void JCUUnitySendMessage(const char *gameObject, const char *method, const char *message);

NS_ASSUME_NONNULL_END
