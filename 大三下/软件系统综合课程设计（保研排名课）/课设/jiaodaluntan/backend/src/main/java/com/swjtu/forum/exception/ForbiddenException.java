package com.swjtu.forum.exception;

public class ForbiddenException extends ApiException {

    public ForbiddenException(String message) {
        super(403, message);
    }
}
