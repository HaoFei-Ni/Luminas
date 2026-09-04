/* luma_status.c — C-ABI 错误码到短句。供测试、日志、绑定异常使用。 */
#include "luma_kv.h"

/* 稳态英文短句；未知码不得返回 NULL，避免日志空指针。 */
const char *luma_strerror(int rc)
{
    switch (rc) {
    case LUMA_OK:
        return "ok";
    case LUMA_ERR_ARG:
        return "invalid argument";
    case LUMA_ERR_NOMEM:
        return "out of memory";
    case LUMA_ERR_NUMERIC:
        return "numeric failure";
    case LUMA_ERR_CUDA:
        return "cuda error";
    case LUMA_ERR_UNSUPPORTED:
        return "unsupported shape or feature";
    default:
        return "unknown error";
    }
}
