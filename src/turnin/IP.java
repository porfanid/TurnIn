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


import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.math.BigInteger;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.URL;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Objects;

/**
 *
 * @author porfanid
 */
public class IP {
    public static int MIN_PORT_NUMBER;
    public static int MAX_PORT_NUMBER;
    
    private static boolean isReady=false;
    
    public static IP REMOTE;
    public static IP LOCAL;
    public static int[] PORTS;
    
    private final InetAddress ip;
    
    private IP(InetAddress ip)
    {
        this.ip=ip;
    }
    
    public IP(String ip) throws UnknownHostException
    {
        this.ip=InetAddress.getByName(ip);
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
        final IP other = (IP) obj;
        return Objects.equals(this.ip, other.ip);
    }

    @Override
    public int hashCode() {
        int hash = 7;
        hash = 59 * hash + Objects.hashCode(this.ip);
        return hash;
    }
    
    
    
    
    
    
    public String getAddress()
    {
        return ip.getHostAddress();
    }
    
    
    
    
    
    
    public static void initialize()
    {
        REMOTE=currentRemote();
        LOCAL=currentLocal();
        PORTS=ports();
        MIN_PORT_NUMBER=0;
        MAX_PORT_NUMBER=65535;
        isReady=true;
    }
    
    private static ArrayList<InetAddress> getRange(InetAddress a,InetAddress b)
    {
        long aToLong=ipTolong(a);
        long bToLong=ipTolong(b);
        ArrayList<InetAddress> list=new ArrayList<>();
        for(long i=aToLong+1;i<bToLong;i++)
        {
            byte[] bytes = BigInteger.valueOf(i).toByteArray();
            try{
                InetAddress address = InetAddress.getByAddress(bytes);
                list.add(address);
            }catch(UnknownHostException e)
            {
                continue;
            }
        }
        return list;
    }
    
    private static final long ipTolong(InetAddress bar)
    {
        //InetAddress bar = InetAddress.getByName(ip);
        ByteBuffer buffer = ByteBuffer.allocate(Long.BYTES).order(ByteOrder.BIG_ENDIAN);
        buffer.put(new byte[] { 0,0,0,0 });
        buffer.put(bar.getAddress());
        buffer.position(0);
        long address = buffer.getLong();
        return address;
    }
    
    private static IP currentRemote()
    {
        try{
            URL whatismyip = new URL("http://checkip.amazonaws.com");
            BufferedReader in = new BufferedReader(new InputStreamReader(whatismyip.openStream()));
            String ip = in.readLine(); //you get the IP as a String
            return new IP(InetAddress.getByName(ip));
        }
        catch(IOException e)
        {
            return null;
        }
    }
    @Override
    public String toString()
    {
        return ip.getHostName();
    }
    
    public static IP currentLocal()
    {
        try{
            DatagramSocket socket = new DatagramSocket();
            socket.connect(InetAddress.getByName("8.8.8.8"), 10002);
            return new IP(socket.getLocalAddress());
        }catch(IOException e)
        {
            return null;
        }
    }
    
    private static int[] ports()
    {
        ArrayList<Integer> list=new ArrayList<>();
        for (int i=MIN_PORT_NUMBER;i<MAX_PORT_NUMBER+1;i++)
        {
            if(available(i))
            {
                list.add(i);
            }
        }
        
        int[] ports=new int[list.size()];
        
        int i=0;
        for(int elem:list)
        {
            ports[i]=elem;
            i++;
        }
        
        return ports;
    }
    
    private static boolean available(int port) {
        if (port < MIN_PORT_NUMBER || port > MAX_PORT_NUMBER) {
            throw new IllegalArgumentException("Invalid start port: " + port);
        }

        ServerSocket ss = null;
        DatagramSocket ds = null;
        try {
            ss = new ServerSocket(port);
            ss.setReuseAddress(true);
            ds = new DatagramSocket(port);
            ds.setReuseAddress(true);
            return true;
        } catch (IOException e) {
        } finally {
            if (ds != null) {
                ds.close();
            }

            if (ss != null) {
                try {
                    ss.close();
                } catch (IOException e) {
                    /* should not be thrown */
                }
            }
        }

        return false;
    }
}