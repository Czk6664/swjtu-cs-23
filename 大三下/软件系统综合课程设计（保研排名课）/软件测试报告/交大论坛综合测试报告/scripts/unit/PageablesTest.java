package com.swjtu.forum.util;

import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Pageable;

import static org.junit.jupiter.api.Assertions.assertEquals;

class PageablesTest {

    @Test
    void ofClampsNegativePageAndOversizedRequest() {
        Pageable pageable = Pageables.of(-3, 500);

        assertEquals(0, pageable.getPageNumber());
        assertEquals(Pageables.MAX_PAGE_SIZE, pageable.getPageSize());
    }

    @Test
    void ofUsesDefaultSizeForInvalidSize() {
        Pageable pageable = Pageables.of(2, 0);

        assertEquals(2, pageable.getPageNumber());
        assertEquals(Pageables.DEFAULT_PAGE_SIZE, pageable.getPageSize());
    }
}
