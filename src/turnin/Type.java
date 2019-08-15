/*
 * The MIT License
 *
 * Copyright 2019 porfanid.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
package turnin;

import java.util.Objects;

/**
 *
 * @author porfanid
 */
public class Type implements Comparable<Type>{

    public static final Type PYTHON=new Type("Python",1,"#!/bin/python");
    public static final Type SHELL=new Type("Shell",2,"#!/bin/bash");
    
    
    @Override
    public int hashCode() {
        int hash = 7;
        hash = 59 * hash + Objects.hashCode(this.type);
        hash = 59 * hash + this.id;
        return hash;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        final Type other = (Type) obj;
        if (this.id != other.id) {
            return false;
        }
        return Objects.equals(this.type, other.type);
    }
    
    
    
    private final String type;
    private final int id;
    public final String command;
    
    private Type(String type, int id,String command)
    {
        this.type=type;
        this.id=id;
        this.command=command;
    }
    public String toString()
    {
        return type;
    }
    public int getId()
    {
        return id;
    }

    @Override
    public int compareTo(Type o) {
        return new Integer(id).compareTo(o.id);
    }
}
